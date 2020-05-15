#This R file can be sourced to provide all of the functions necessary to produce k-extended LHCs (Williamson, 2015). The last two lines in this file can be uncommented out and they will generate the same type of orthogonal maximin LHC used to compare performance against sliced LHCs in section 3.1. For further information on how to use the code, please contact Danny Williamson.

require(lhs)
#require(DoE.wrapper)
#require(DiceDesign)
#require(parallel)
toInts <- function(LH){
  n <- length(LH[,1])
  ceiling(n*LH)
}

RhoSq <- function(LH){
  A <- cor(LH)
  m <- dim(LH)[2]
  2*sum(A[upper.tri(A)]^2)/(m*(m-1))
}

oneColDist <- function(LH, whichCol, k){
  D <- dist(LH[,whichCol],method="manhattan")
  D[D==0] <- 1/k
  D
}

oneColDist <- function(LH, whichCol, k){
  D <- dist(LH[,whichCol],method="manhattan")
  D[D==0] <- 1/k
  D
}


newphiP <- function(LH, k, p){
  tD <- oneColDist(LH,1,k)
  for(i in 2:(dim(LH)[2])){
    tD <- tD + oneColDist(LH,i,k)
  }
  sum(tD^(-p))^(1/p)
}

dbar <- function(n,m,k,tc){
  (m*n*tc*(tc*k*(n^2-1) + 3*(tc-1)))/(6*k*choose(tc*n,2))
}

newphiPL <- function(n, k, bard, p){
  choose(k*n,2)^(1/p)/bard
}

newphiPU <- function(n, m, k, p, tc){
  ((n*k^(p)*tc*(tc-1))/(2*m) + sum( tc^2*(n-c(1:(n-1)))/(m*c(1:(n-1))^p)))^(1/p)
}

objectiveFun <- function(LH, w, p, phiU, phiL, k){
  rho <- RhoSq(LH)
  phiP <- newphiP(LH, k, p)
  w*rho + (1-w)*(phiP - phiL)/(phiU-phiL)
}

newphiL1 <- function(n, bard, p){
  upp <- ceiling(bard)
  low <- floor(bard)
  (choose(n,2)*(((upp - bard)/low^p) + ((bard - low)/upp^p)))^(1/p)
}

Sim.anneal.k <- function(tLHS, tc, k, n, m, w, p, Imax=1000, FAC_t=0.9, t0=NULL){
  Dcurrent <- tLHS
  tbard <- dbar(n=n,m=m,k=k,tc=tc)
  phiU <- newphiPU(n=n, m=m, k=k, p=p, tc=tc)
  if(tc<2)
    phiL <- newphiL1(n=n, bard=tbard, p=p)
  else
    phiL <- newphiPL(n=n, k=k, bard=tbard, p=p)
  if(is.null(t0)){
    delta <- 1/k
    rdis <- runif(n=choose(tc*n,2), min = 0.5*tbard, max=1.5*tbard)
    t0curr <- sum(rdis^(-p))^(1/p)
    rdis[which.min(rdis)] <- rdis[which.min(rdis)] - delta
    t0new <- sum(rdis^(-p))^(1/p)
    t0 <- (-1)*(t0new - t0curr)/log(0.99)
  }
  psiDcurrent <- objectiveFun(Dcurrent, w=w, p=p, phiU=phiU, phiL=phiL, k=k)
  Dbest <- Dcurrent
  psiDbest <- psiDcurrent
  FLAG <- 1
  t <- t0
  while(FLAG==1){
    FLAG <- 0
    I <- 1
    while(I < Imax){
      Dtry <- Dcurrent
      j <- sample(1:m, 1)
      i12 <- sample(c(((tc-1)*n+1):(tc*n)),2,replace=FALSE)
      Dtry[i12,j] <- Dcurrent[c(i12[2],i12[1]),j]
      psiDtry <- objectiveFun(Dtry, w=w, p=p, phiU=phiU, phiL=phiL, k=k)
      if(psiDtry < psiDcurrent){
        Dcurrent <- Dtry
        psiDcurrent <- psiDtry
        FLAG <- 1
      }
      else if((runif(1) < exp(-(psiDtry - psiDcurrent)/t))&(psiDtry!=psiDcurrent)){
        Dcurrent <- Dtry
        psiDcurrent <- psiDtry
        FLAG <- 1
      }
      if(psiDtry < psiDbest){
        Dbest <- Dtry
        psiDbest <- psiDtry
        print(paste("New Dbest with psi = ", psiDbest, " found, reset I from I = ", I, sep=""))
        I <- 1
      }
      else{
        I <- I + 1
      }
    }
    t <- t*FAC_t
    print(t)
  }
  Dbest
}

FirstRankLHS <- function(n, m, p, w, Imax){
  tLHS <- randomLHS(n,m)
  tLHS <- apply(tLHS, 2, order)
  Sim.anneal.k(tLHS=tLHS, tc=1, k=1, n=n, m=m, w=w, p=p, Imax=Imax, FAC_t=0.8, t0=NULL)
}

MakeValidNewLHS <- function(CurrentBig, n, m, k){
  if(k*n <= n^m){
    Found <- FALSE
    while(!Found){
      anLHC <- apply(randomLHS(n,m),2,order)
      if(!any(dist(rbind(CurrentBig,anLHC), method="manhattan")==0))
        Found <- TRUE
    }
  }
  else{
    anLHC <- apply(randomLHS(n,m),2,order)
  }
  return(anLHC)
}

MakeRankExtensionCubes <- function(n, m, k, w, p=50, FAC_t=0.8, startLHS=NULL, Imax=1000){
  if(is.null(startLHS))
    lhs1 <- FirstRankLHS(n, m, p, w,Imax=Imax)
  else
    lhs1 <- as.matrix(toInts(startLHS))
  BigExtendedMatrix <- matrix(NA, nrow=k*n, ncol=m)
  BigExtendedMatrix[1:n,] <- lhs1
  for(i in 2:k){
    print(paste("Current extension = ", i, " of ", k, sep=""))
    newLHC <- MakeValidNewLHS(BigExtendedMatrix[1:((i-1)*n),],n=n,m=m,k=i)
    BigExtendedMatrix[((i-1)*n + 1):(i*n),] <- newLHC
    BigExtendedMatrix[1:(i*n),] <- Sim.anneal.k(tLHS=BigExtendedMatrix[1:(i*n),], tc=i, k=k, n=n, m=m, w=w, p=p, Imax=Imax, FAC_t=FAC_t, t0=NULL)
  }
  lapply(1:k, function(e) BigExtendedMatrix[(1+(e-1)*n):(e*n),]) 
}

oneIN <- function(LHcolumn,left,right){
  any(which(LHcolumn>=left)%in%which(LHcolumn<right))
}

manyIN <- Vectorize(oneIN, c("left","right"))

getPointers <- function(rankLHCrow,currentExtendedLHC, n, d, increment,k){
  leftmostedges <- (rankLHCrow-1)/n
  tleftmosts <- matrix(leftmostedges,nrow=k+1,ncol=d,byrow=T)
  leftedges <- matrix(rep(0:k,d),nrow=k+1,ncol=d)
  leftedges <- leftedges*increment + tleftmosts
  rightedges <- leftedges+increment
  sapply(1:d, function(j) which(manyIN(currentExtendedLHC[,j],leftedges[,j],rightedges[,j])))
}

sampleNewPoint <- function(pointersRow, rankLHCrow, increment, n, d, k){
  location <- runif(d)
  if(length(pointersRow[,1]) < k)
    newPoint <- sapply(1:d, function(j) sample(c(1:(k+1))[-pointersRow[,j]],1))
  else
    newPoint <- sapply(1:d, function(j) c(1:(k+1))[-pointersRow[,j]])
  (rankLHCrow-1)/n + (newPoint-1)*increment  + increment*location
}

#LHCmaster is a starting LHC on [0,1]^d. If NULL, it is generated from rankLHClist[[1]]
NewExtendingLHS <- function(rankLHClist, LHCmaster=NULL){
  #there are k+1 rank LHCs in rankLHClist, which can be constructed using MakeRankExtensionCubes
  k <- length(rankLHClist) -1
  tdims <- dim(rankLHClist[[1]])
  n <- tdims[1]
  d <- tdims[2]
  increment=1/(n*(k+1))
  if(is.null(LHCmaster)){
    LHCmaster <- rankLHClist[[1]]
    LHCmaster <- (LHCmaster + runif(n*d) - 1)/n
  }
  pointers <- mclapply(1:n, function(e) {getPointers(rankLHClist[[2]][e,], LHCmaster,n=n,d=d,increment=increment,k=k)})
  pointers <- lapply(pointers, function(e) {dim(e) <- c(1,d);e})
  NewLHC1 <- t(sapply(1:n, function(l) sampleNewPoint(pointers[[l]], rankLHClist[[2]][l,], increment, n, d, k)))
  ExtendedLHC <- matrix(NA, nrow=n*(k+1), ncol=d)
  ExtendedLHC[1:n,] <- LHCmaster
  ExtendedLHC[(n+1):(2*n),] <- NewLHC1
  if(k>2){
    for(l in 3:(k+1)){
      pointers <- mclapply(1:n, function(e) getPointers(rankLHClist[[l]][e,],na.omit(ExtendedLHC),n=n,d=d,increment=increment,k=k))
      newLHC <- t(sapply(1:n, function(j) sampleNewPoint(pointers[[j]],rankLHClist[[l]][j,], increment, n,d,k)))
      ExtendedLHC[((l-1)*n+1):(l*n),] <- newLHC
    }
  }
  ExtendedLHC
}


#testcube <- MakeRankExtensionCubes(n=8,m=2,k=5,w=0.2, FAC_t=0.5)
#newExtended <- NewExtendingLHS(testcube)

