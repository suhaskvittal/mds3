1. Build Dramsim3

```
cd DRAMsim3
mkdir -p build
cd build
cmake ..
make -j
cd ../../
```

2. Build sim_dramsim3
```
cd src
make dramsim3
```

3. Running without RFM
```
./sim_dramsim3 -inst_limit 100000000 ../TRACES/mcf_17.mtf.gz
```

4. Running with RFM
```
./sim_dramsim3 -inst_limit 100000000 -enablerfm ../TRACES/mcf_17.mtf.gz
```

5. Dramsim3 config files
```
cd src/dramsim3cfg
```
