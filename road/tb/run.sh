python3 analysis_mc.py -f ../../../test_ntuples/MuonGun_1k_eta_All//MuonGE0Segments.root -t digi -b all -v -p 0 -o 2
mv *.pdf *.root output_log_digi_bxall_crosspart_partial_or2.txt Results_pattern_effi/MuonGun/

python3 analysis_mc.py -f ../../../test_ntuples/MuonGun+MinBias_1k_eta_All//MuonGE0Segments.root -t digi -b all -v -p 140 -o 2
mv *.pdf *.root output_log_digi_bxall_crosspart_partial_or2.txt Results_pattern_effi/MuonGun_MinBias/
