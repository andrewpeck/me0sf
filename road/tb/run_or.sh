python3 analysis_mc.py -f ../../../test_ntuples/MuonGun_1k_eta_All/MuonGE0Segments.root -t digi -b all -v -p 0 -o 2
mv *.txt *.root *.pdf Results_OR/MuonGun/

python3 analysis_mc.py -f ../../../test_ntuples/MuonGun_1k_eta_All/MuonGE0Segments.root -t digi -b all -v -p 0 -o 4
mv *.txt *.root *.pdf Results_OR/MuonGun/

python3 analysis_mc.py -f ../../../test_ntuples/MuonGun_1k_eta_All/MuonGE0Segments.root -t digi -b all -v -p 0 -o 8
mv *.txt *.root *.pdf Results_OR/MuonGun/

python3 analysis_mc.py -f ../../../test_ntuples/MuonGun_1k_eta_All/MuonGE0Segments.root -t digi -b all -v -p 0 -o 16
mv *.txt *.root *.pdf Results_OR/MuonGun/


python3 analysis_mc.py -f ../../../test_ntuples/MuonGun+MinBias_1k_eta_All/MuonGE0Segments.root -t digi -b all -v -p 140 -o 2
mv *.txt *.root *.pdf Results_OR/MuonGun_MinBias/

python3 analysis_mc.py -f ../../../test_ntuples/MuonGun+MinBias_1k_eta_All/MuonGE0Segments.root -t digi -b all -v -p 140 -o 4
mv *.txt *.root *.pdf Results_OR/MuonGun_MinBias/

python3 analysis_mc.py -f ../../../test_ntuples/MuonGun+MinBias_1k_eta_All/MuonGE0Segments.root -t digi -b all -v -p 140 -o 8
mv *.txt *.root *.pdf Results_OR/MuonGun_MinBias/

python3 analysis_mc.py -f ../../../test_ntuples/MuonGun+MinBias_1k_eta_All/MuonGE0Segments.root -t digi -b all -v -p 140 -o 16
mv *.txt *.root *.pdf Results_OR/MuonGun_MinBias/
