#pragma once

#include <vector>
#include "channel_state.h"
#include "common.h"
#include "configuration.h"

namespace dramsim3 {

class Refresh {
   public:
    Refresh(const Config& config, ChannelState& channel_state);
    void ClockTick();

   private:
    uint64_t clk_;
    int refresh_interval_;
    int trefi_cnt_ =0;

    const Config& config_;
    ChannelState& channel_state_;
    RefreshPolicy refresh_policy_;

    int next_rank_, next_bg_, next_bank_;

    void InsertRefresh();

    void IterateNext();
};

}  // namespace dramsim3
