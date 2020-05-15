source("kExtendedLHCs.R")
Rep_Ens_Size <- 25
Nreps <- 5
HowManyCubes <- 4
Param_Names <- c("incubation_time", "infectious_time", 
                 "r_zero", "lock_1_restrict", "lock_2_release")
New_cube <- MakeRankExtensionCubes(n=Rep_Ens_Size, m=length(Param_Names), 
                                   k=HowManyCubes, w=0.2, FAC_t=0.5)
newExtended <- NewExtendingLHS(New_cube)
newExtended
pairs(newExtended, col=c(rep(2,Rep_Ens_Size),rep(3,Rep_Ens_Size*(HowManyCubes-1))), pch=16)
newExtended <- 2*newExtended - 1
colnames(newExtended) <- Param_Names
EnsembleDesign <- as.data.frame(newExtended)
EnsembleDesign <- cbind(EnsembleDesign, Repeats=c(rep(Nreps,Rep_Ens_Size), rep(1,Rep_Ens_Size*(HowManyCubes-1))))
head(EnsembleDesign)
ExampleEnsembleDesign <- EnsembleDesign
save(ExampleEnsembleDesign, file= "ExampleEnsembleDesign.RData")
