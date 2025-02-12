#include "bankstate.h"

#include <random>

namespace dramsim3 {

///////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////

static std::mt19937_64 rng(0);
static bool pac_next_pre_cmd_is_valid = false;
static CommandType pac_next_pre_cmd;

///////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////

BankState::BankState(const Config& config, SimpleStats& simple_stats, int rank, int bank_group, int bank)
    :   config_(config),
        simple_stats_(simple_stats),
        state_(State::CLOSED),
        cmd_timing_(static_cast<int>(CommandType::SIZE)),
        open_row_(-1),
        row_hit_count_(0),
        rank_(rank),
        bank_group_(bank_group),
        bank_(bank),
        raa_ctr_(0),
        acts_counter_(0),
        total_row_acts_(config_.rows, 0),
        prac_(config_.rows, 0),
        moat_eth_( config.moat_ath / 2 ),
        moat_ath_( config.moat_ath ),
        mopac_mint_sel_(rng() % config_.pac_prob),
        ref_idx_(0)
{
    cmd_timing_[static_cast<int>(CommandType::READ)] = 0;
    cmd_timing_[static_cast<int>(CommandType::READ_PRECHARGE)] = 0;
    cmd_timing_[static_cast<int>(CommandType::WRITE)] = 0;
    cmd_timing_[static_cast<int>(CommandType::WRITE_PRECHARGE)] = 0;
    cmd_timing_[static_cast<int>(CommandType::ACTIVATE)] = 0;
    cmd_timing_[static_cast<int>(CommandType::PRECHARGE)] = 0;
    cmd_timing_[static_cast<int>(CommandType::REFRESH_BANK)] = 0;
    cmd_timing_[static_cast<int>(CommandType::REFsb)] = 0;
    cmd_timing_[static_cast<int>(CommandType::REFab)] = 0;
    cmd_timing_[static_cast<int>(CommandType::SREF_ENTER)] = 0;
    cmd_timing_[static_cast<int>(CommandType::SREF_EXIT)] = 0;
    cmd_timing_[static_cast<int>(CommandType::RFMsb)] = 0; // [RFM] Same Bank RFM
    cmd_timing_[static_cast<int>(CommandType::RFMab)] = 0; // [RFM] All Bank RFM

    cmd_timing_[static_cast<int>(CommandType::READ_PRECHARGE2)] = 0;
    cmd_timing_[static_cast<int>(CommandType::WRITE_PRECHARGE2)] = 0;
    cmd_timing_[static_cast<int>(CommandType::PRECHARGE2)] = 0;

    // [Stats]
    acts_stat_name_ = "acts." + std::to_string(rank_) + "." + std::to_string(bank_group_) + "." + std::to_string(bank_);    
    simple_stats_.InitStat(acts_stat_name_, "counter", "ACTs Counter");
}

///////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////

CommandType
GetPrechargeCmd(int pac_prob=1) {
#if USE_PRAC==PRAC_IMPL_MOPAC
    return CommandType::PRECHARGE;
#elif USE_PRAC==PRAC_IMPL_PAC
    if (!pac_next_pre_cmd_is_valid) {
        pac_next_pre_cmd_is_valid = true;
        if (rng() % pac_prob == 0) pac_next_pre_cmd = CommandType::PRECHARGE2;
        else                       pac_next_pre_cmd = CommandType::PRECHARGE;
    }
    return pac_next_pre_cmd;
#elif USE_PRAC>=1
    return CommandType::PRECHARGE2;
#else
    return CommandType::PRECHARGE;
#endif
}

Command
BankState::GetReadyCommand(const Command& cmd, uint64_t clk) const {
    CommandType required_type = CommandType::SIZE;
    switch (state_) {
        case State::CLOSED:
            switch (cmd.cmd_type) {
                // The state is closed and we need to activate the row to read/write
                case CommandType::READ:
                case CommandType::READ_PRECHARGE:
                case CommandType::READ_PRECHARGE2:
                case CommandType::WRITE:
                case CommandType::WRITE_PRECHARGE:
                case CommandType::WRITE_PRECHARGE2:
                    // [RFM] Block ACTs if RAA Counter == RAAMMT
                    // Don't block all banks, just the bank that wants to launch the command
                    if (config_.rfm_mode == 1 && raa_ctr_ >= config_.raammt) {
                        required_type = CommandType::RFMsb;
                    } else if (config_.rfm_mode == 2 && raa_ctr_ >= config_.raammt) {
                        required_type = CommandType::RFMab;
                    } else {
                        required_type = CommandType::ACTIVATE;
                    }
                    break;
                // The state is closed so we can issue and refresh commands
                case CommandType::REFRESH_BANK:
                case CommandType::REFsb:
                case CommandType::REFab:
                case CommandType::SREF_ENTER:
                case CommandType::RFMsb: // [RFM] Same Bank RFM
                case CommandType::RFMab: // [RFM] All Bank RFM
                    required_type = cmd.cmd_type;
                    break;
                default:
                    std::cerr << "Unknown type!" << std::endl;
                    AbruptExit(__FILE__, __LINE__);
                    break;
            }
            break;
        case State::OPEN:
            switch (cmd.cmd_type) {
                // The state is open and we get a RB hit if the row is the same else we PRECHARGE first
                case CommandType::READ:
                case CommandType::READ_PRECHARGE:
                case CommandType::READ_PRECHARGE2:
                case CommandType::WRITE:
                case CommandType::WRITE_PRECHARGE:
                case CommandType::WRITE_PRECHARGE2:
                    if (cmd.Row() == open_row_) {
                        required_type = cmd.cmd_type;
#if defined(ROWPRESS)
                        // Forced row closure
                        if (clk - row_open_clk_ > config_.tON) {
                            bool pre2 = GetPrechargeCmd(config_.pac_prob) == CommandType::PRECHARGE2;
                            if (pre2) {
                                required_type = (required_type == CommandType::READ) ?
                                                CommandType::READ_PRECHARGE2 : CommandType::WRITE_PRECHARGE2;
                            } else {
                                required_type = (required_type == CommandType::READ) ?
                                                CommandType::READ_PRECHARGE : CommandType::WRITE_PRECHARGE;
                            }
                        }
#endif
                    } else {
                        required_type = GetPrechargeCmd(config_.pac_prob);
                    }
                    break;
                // The state is open and a precharge command is issued to closed the row to perform refresh
                // TODO: Use PREsb and PREab here
                case CommandType::REFRESH_BANK:
                case CommandType::REFsb:
                case CommandType::REFab:  
                case CommandType::SREF_ENTER:
                case CommandType::RFMsb: // [RFM] Same Bank RFM
                case CommandType::RFMab: // [RFM] All Bank RFM
                    required_type = GetPrechargeCmd(config_.pac_prob);
                    break;
                default:
                    std::cerr << "Unknown type!" << std::endl;
                    AbruptExit(__FILE__, __LINE__);
                    break;
            }
            break;
        case State::SREF:
            switch (cmd.cmd_type) {
                // The state is SREF and to read/write we need to exit SREF using SREF_EXIT
                case CommandType::READ:
                case CommandType::READ_PRECHARGE:
                case CommandType::READ_PRECHARGE2:
                case CommandType::WRITE:
                case CommandType::WRITE_PRECHARGE:
                case CommandType::WRITE_PRECHARGE2:
                    required_type = CommandType::SREF_EXIT;
                    break;
                default:
                    std::cerr << "Unknown type!" << std::endl;
                    AbruptExit(__FILE__, __LINE__);
                    break;
            }
            break;
        case State::PD:
        case State::SIZE:
            std::cerr << "In unknown state" << std::endl;
            AbruptExit(__FILE__, __LINE__);
            break;
    }

    if (required_type != CommandType::SIZE) {
        if (clk >= cmd_timing_[static_cast<int>(required_type)]) {
            return Command(required_type, cmd.addr, cmd.hex_addr);
        }
    }
    return Command();
}

///////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////

// 0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, >= 1024
uint32_t get_geostat_bin(uint16_t val) {
    if (val == 0) return 0;
    if (val == 1) return 1;
    if (val <= 2) return 2;
    if (val <= 4) return 3;
    if (val <= 8) return 4;
    if (val <= 16) return 5;
    if (val <= 32) return 6;
    if (val <= 64) return 7;
    if (val <= 128) return 8;
    if (val <= 256) return 9;
    if (val <= 512) return 10;
    if (val <= 1024) return 11;
    return 12;
}

void BankState::UpdateState(const Command& cmd, uint64_t clk) {
    switch (state_) {
        case State::OPEN:
            switch (cmd.cmd_type) {
                case CommandType::READ:
                case CommandType::WRITE:
                    row_hit_count_++;
                    break;
                // The state was open and a precharge command was issued which closed the row
                case CommandType::READ_PRECHARGE2:
                case CommandType::WRITE_PRECHARGE2:
                case CommandType::PRECHARGE2:
                    // Update act counter.
                    ++prac_[ open_row_ ];
#if USE_PRAC==PRAC_IMPL_MOAT || USE_PRAC==PRAC_IMPL_PAC
                    MoatUpdate();
#endif
                case CommandType::READ_PRECHARGE:
                case CommandType::WRITE_PRECHARGE:
                case CommandType::PRECHARGE:
                    pac_next_pre_cmd_is_valid = false;
#if defined(ROWPRESS) && USE_PRAC==PRAC_IMPL_MOPAC
                    MopacHandleRowpress(clk);
#endif
                    state_ = State::CLOSED;
                    open_row_ = -1;
                    row_hit_count_ = 0;
                    break;
                case CommandType::ACTIVATE:
                case CommandType::REFRESH_BANK:
                case CommandType::REFsb:
                case CommandType::REFab:
                case CommandType::SREF_ENTER:
                case CommandType::SREF_EXIT:
                case CommandType::RFMsb: // [RFM] Same Bank RFM
                case CommandType::RFMab: // [RFM] All Bank RFM
                default:
                    AbruptExit(__FILE__, __LINE__);
            }
            break;
        case State::CLOSED:
            switch (cmd.cmd_type) {
                case CommandType::REFab:
                case CommandType::REFRESH_BANK:
                case CommandType::REFsb:
#if USE_PRAC==PRAC_IMPL_MOPAC
                    // Do MOPAC logic here so if any counters of refreshed rows are increment by
                    // MOPAC, they immediately get reset.
                    MopacHandleRef();
#endif
                    for (int i = 0; i < config_.rows_refreshed; i++) {
                        int idx = (ref_idx_ + i) % config_.rows;
                        simple_stats_.IncrementVec("prac_per_tREFI", get_geostat_bin(prac_[idx]));
                        prac_[idx] = 0;
                    }
                    simple_stats_.IncrementVec("acts_per_tREFI", acts_counter_/10);

                    raa_ctr_ -= std::min<int>(raa_ctr_, config_.ref_raa_decrement);
                    acts_counter_ = 0;
#if USE_PRAC==PRAC_IMPL_MOAT || USE_PRAC==PRAC_IMPL_PAC
                    MoatHandleRef();
#endif
                    ref_idx_ = (ref_idx_ + config_.rows_refreshed) % config_.rows;
                    if (ref_idx_ == 0) {
                        total_row_acts_.clear();
                    }
                    break;
                case CommandType::RFMab: // [RFM] All Bank RFM
                case CommandType::RFMsb: // [RFM] Same Bank RFM, cannot be used with PRAC+ABO
                    raa_ctr_ -= std::min<int>(raa_ctr_, config_.rfm_raa_decrement);
#if USE_PRAC==PRAC_IMPL_MOPAC
                    MopacMitigate();
#elif USE_PRAC==PRAC_IMPL_MOAT || USE_PRAC==PRAC_IMPL_PAC
                    MoatMitigate();
#endif
                    break;
                // The state was closed and an activate command was issued which opened the row
                case CommandType::ACTIVATE:
                    state_ = State::OPEN;
                    open_row_ = cmd.Row();
                    row_open_clk_ = clk;
                    // [Stats]
                    acts_counter_++;
                    simple_stats_.Increment(acts_stat_name_);

                    total_row_acts_[open_row_]++;
                    if (total_row_acts_[open_row_] == 32) simple_stats_.Increment("rows_ge_32_acts");
                    if (total_row_acts_[open_row_] == 64) simple_stats_.Increment("rows_ge_64_acts");
                    if (total_row_acts_[open_row_] == 128) simple_stats_.Increment("rows_ge_128_acts");
                    if (total_row_acts_[open_row_] == 200) simple_stats_.Increment("rows_ge_200_acts");
                    if (total_row_acts_[open_row_] == 256) simple_stats_.Increment("rows_ge_256_acts");
                    // [RFM]
                    raa_ctr_++;
#if USE_PRAC==PRAC_IMPL_MOPAC
                    MopacCtrUpdate();
#endif
                    break;
                // The state was closed and a refresh command was issued which changed the state to SREF
                case CommandType::SREF_ENTER:
                    state_ = State::SREF;
                    break;
                case CommandType::READ:
                case CommandType::WRITE:
                case CommandType::READ_PRECHARGE:
                case CommandType::READ_PRECHARGE2:
                case CommandType::WRITE_PRECHARGE:
                case CommandType::WRITE_PRECHARGE2:
                case CommandType::PRECHARGE:
                case CommandType::PRECHARGE2:
                case CommandType::SREF_EXIT:
                default:
                    std::cout << cmd << std::endl;
                    AbruptExit(__FILE__, __LINE__);
            }
            break;
        case State::SREF:
            switch (cmd.cmd_type) {
                // The state was SREF and a SREF_EXIT command was issued which changed the state to closed
                case CommandType::SREF_EXIT:
                    state_ = State::CLOSED;
                    break;
                case CommandType::READ:
                case CommandType::WRITE:
                case CommandType::READ_PRECHARGE:
                case CommandType::WRITE_PRECHARGE:
                case CommandType::PRECHARGE2:
                case CommandType::ACTIVATE:
                case CommandType::PRECHARGE:
                case CommandType::REFRESH_BANK:
                case CommandType::REFsb:
                case CommandType::REFab:
                case CommandType::SREF_ENTER:
                case CommandType::RFMsb: // [RFM] Same Bank RFM
                case CommandType::RFMab: // [RFM] All Bank RFM
                default:
                    AbruptExit(__FILE__, __LINE__);
            }
            break;
        default:
            AbruptExit(__FILE__, __LINE__);
    }
    return;
}

///////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////

void BankState::UpdateTiming(CommandType cmd_type, uint64_t time) {
    cmd_timing_[static_cast<int>(cmd_type)] =
        std::max(cmd_timing_[static_cast<int>(cmd_type)], time);
    return;
}

///////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////

std::string BankState::StateToString(State state) const {
    switch (state) {
        case State::OPEN:
            return "OPEN";
        case State::CLOSED:
            return "CLOSED";
        case State::SREF:
            return "SREF";
        case State::PD:
            return "PD";
        case State::SIZE:
            return "SIZE";
    }
    return "UNKNOWN";
}

void BankState::PrintState() const {
    std::cout << "State: " << StateToString(state_) << std::endl;
    std::cout << "Open Row: " << open_row_ << std::endl;
    std::cout << "Row Hit Count: " << row_hit_count_ << std::endl;
    std::cout << "RAA Counter: " << raa_ctr_ << std::endl;

    // Print the timing constraints
    for (int i = 0; i < static_cast<int>(CommandType::SIZE); i++) {
        std::cout << "Command: " << CommandTypeToString(static_cast<CommandType>(i)) << " Time: " << cmd_timing_[i] << std::endl;
    }
}

///////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////

bool
BankState::CheckAlert() {
    if (mopac_critical_rows_ > 0) {
        simple_stats_.Increment("num_mopac_alerts_qth");
        return true;
    } else if (mopac_buf_.size() >= config_.mopac_buf_size) {
        simple_stats_.Increment("num_mopac_alerts_buf_full");
        return true;
    } else if (moat_row_valid_) {
        if (prac_[moat_row_] >= moat_ath_) {
            return true;
        }
    }
    return false;
}

///////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////

void
BankState::MoatCheckTrackedRowIsRefreshed() {
    size_t lwr = ref_idx_,
           upp = ref_idx_ + config_.rows_refreshed;
    if (moat_row_valid_ && moat_row_ >= lwr && moat_row_ < upp) {
        moat_row_valid_ = false;
    }
}

void
BankState::MoatUpdate() {
    size_t c = prac_[open_row_];
    if (c >= moat_eth_ && (!moat_row_valid_ || c > prac_[moat_row_])) {
        // Need to send immediate alert.
        moat_row_ = open_row_;
        moat_row_valid_ = true;
    }
}

void
BankState::MoatMitigate() {
    if (moat_row_valid_) {
        prac_[ moat_row_ ] = 0;
        moat_row_valid_ = false;
        simple_stats_.Increment("num_moat_mitigations");
    }
}

void
BankState::MoatHandleRef() {
    ++moat_trefi_cnt_;
    // If this is the 5th tREFI, perform a mitigation.
    if (moat_trefi_cnt_ == 5) {
        MoatMitigate();
        moat_trefi_cnt_ = 0;
    }
    // If tracked row is refreshed, update the counter
    MoatCheckTrackedRowIsRefreshed();
}

///////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////

void SafeDecrement(size_t x) { if (x) --x; }

void
BankState::MopacUpdatePRAC(size_t r, size_t by) {
    prac_[r] += by;
    if (prac_[r] >= moat_eth_ && (!moat_row_valid_ || prac_[r] > prac_[moat_row_])) {
        moat_row_ = r;
        moat_row_valid_ = true;
    }
}

void
BankState::MopacFlushNextCtr() {
    if (mopac_buf_.empty()) return;
    MopacEntry e = mopac_buf_.front();
    mopac_buf_.pop_front();
    MopacUpdatePRAC(e.row_, e.sctr_);
}

void
BankState::MopacFlushAllCtrs() {
    for (size_t i = 0; i < config_.mopac_abo_updates; i++) {
        MopacFlushNextCtr();
    }
}

void
BankState::MopacHandleCriticalRow() {
    for (auto it = mopac_buf_.begin(); it != mopac_buf_.end(); ) {
        if (it->sctr_ >= config_.mopac_queue_th) {
            MopacUpdatePRAC(it->row_, it->sctr_);
            it = mopac_buf_.erase(it);
            SafeDecrement(mopac_critical_rows_);
            break;
        } else {
            ++it;
        }
    }
}

void
BankState::MopacHandleRef() {
    // First, handle rows that will be refreshed -- remove
    // them from `mopac_buf` and `mopac_mint_window`.
    size_t lwr = ref_idx_,
           upp = ref_idx_+config_.rows_refreshed;
    for (auto it = mopac_buf_.begin(); it != mopac_buf_.end(); ) {
        if (it->row_ >= lwr && it->row_ < upp) {
            if (it->sctr_ >= config_.mopac_queue_th) {
                SafeDecrement(mopac_critical_rows_);
            }
            it = mopac_buf_.erase(it);
        } else {
            ++it;
        }
    }

    if (mopac_drain_countdown_ == 0) {
        for (size_t i = 0; i < config_.mopac_ref_updates; i++) {
            MopacFlushNextCtr();
        }
        mopac_drain_countdown_ = config_.mopac_drain_freq;
    }
    --mopac_drain_countdown_;

    MoatCheckTrackedRowIsRefreshed();
}

void
BankState::MopacMitigate() {
    // SO this will occur during RFMab. For MOPAC, we will hijack the use of
    // RFMab to simply update counters.
    if (mopac_critical_rows_ > 0) {
        MopacHandleCriticalRow();
    } else if (mopac_buf_.size() >= config_.mopac_buf_size) {
        MopacFlushAllCtrs();
    } else if (moat_row_valid_ && prac_[moat_row_] >= moat_ath_) {
        MoatMitigate();
    } else {
        MopacFlushAllCtrs();
    }
}

void
BankState::MopacCtrUpdate() {
    auto eit = mopac_buf_.end();
    for (auto it = mopac_buf_.begin(); it != mopac_buf_.end(); it++) {
        if (it->row_ == open_row_) {
            eit = it;
            break;
        }
    }

    if (mopac_act_ctr_ == mopac_mint_sel_) {
        if (eit == mopac_buf_.end()) {
            MopacEntry e = { open_row_, 1, 1 };
            mopac_buf_.push_back(e);
        } else {
            ++eit->sctr_;
            if (eit->sctr_ == config_.mopac_queue_th) {
                ++mopac_critical_rows_;
            }
        }
        // Check if entry is already in mopac_buf.
        simple_stats_.Increment("num_mopac_buf_ins");
    }
    if ((++mopac_act_ctr_) == config_.pac_prob) {
        mopac_act_ctr_ = 0;
        mopac_mint_sel_ = rng() % config_.pac_prob;
    }
}

///////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////

void
BankState::MopacHandleRowpress(uint64_t clk) {
    bool found = false;
    for (auto it = mopac_buf_.begin(); it != mopac_buf_.end(); it++) {
        if (it->row_ == open_row_) {
            found = true;
            break;
        }
    }
    if (!found) return;

    uint64_t clk_on = clk - row_open_clk_;
    size_t n_acts = ((size_t) ceil( ((double)clk_on) / ((double)config_.tON) )) - 1;
    
    simple_stats_.AddValue("row_open_time", n_acts);

    while (n_acts--) {
        MopacCtrUpdate();
    }
}

///////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////

}  // namespace dramsim3

///////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////
