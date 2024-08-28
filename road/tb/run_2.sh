
python3 analysis_mc.py -f ../../../test_ntuples/MuonGun+MinBias_1k_eta_All/MuonGE0Segments.root -t digi -b all -v -p 140 -c none
mv *.txt *.root *.pdf Results_cross_partition/MuonGun_MinBias_PU140_BX00/

python3 analysis_mc.py -f ../../../test_ntuples/NeutrinoGun+MinBias_PU200/MuonGE0Segments.root -t digi -b all -v -p 200 -c none
python3 analysis_mc.py -f ../../../test_ntuples/NeutrinoGun+MinBias_PU200/MuonGE0Segments.root -t digi -b all -v -p 200 -c partial
python3 analysis_mc.py -f ../../../test_ntuples/NeutrinoGun+MinBias_PU200/MuonGE0Segments.root -t digi -b all -v -p 200 -c full
mv *.txt *.root *.pdf Results_cross_partition/NeutrinoGun_MinBias_PU200/
