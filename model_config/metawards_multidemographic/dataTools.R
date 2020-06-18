## @knitr convertDesignToInput
## function to convert from design to input space
convertDesignToInput <- function(design, parRanges, scale = c("zero_one", "negone_one")) {
  
    ## ACTUAL CODE WILL HAVE CHECKS ON INPUTS HERE 
    require(dplyr)
    require(tidyr)
  
    ## convert from design space to input space
    input <- mutate(design, ind = 1:n()) %>%
        gather(parameter, value, -ind) %>%
        left_join(parRanges, by = "parameter")
    if(scale[1] == "negone_one") {
        input <- mutate(input, value = value / 2 + 1)
    }
    input <- mutate(input, value = value * (upper - lower) + lower) %>%
        dplyr::select(ind, parameter, value) %>%
        spread(parameter, value) %>%
        arrange(ind) %>%
        dplyr::select(-ind)
    
    ## return inputs
    input
}

## @knitr convertInputToDisease
## function to convert from input to disease space
convertInputToDisease <- function(input, repeats) {
  
    ## ACTUAL CODE WILL HAVE CHECKS ON INPUTS HERE 
    require(dplyr)
    
    ## common parameters to all pathways
    disease <- tibble(`beta[2]` = input$r_zero / input$infectious_time)
    disease$`beta[3]` <- disease$`beta[2]`
    disease$`progress[0]` <- 1
    disease$`progress[1]` <- 1 - exp(-(1 / (input$incubation_time - 1)))
    disease$`progress[2]` <- 1
    disease$`progress[3]` <- 1 - exp(-(1 / (input$infectious_time - 1)))
    disease$`.lock_1_restrict` <- input$lock_1_restrict
    disease$`.lock_2_release` <- input$lock_2_release
    
    ## hospital progression
    disease$`hospital:progress[2]` <- 1
    disease$`hospital:progress[3]` <- 1 - exp(-(1 / (input$hospital_time - 1)))
    
    ## critical care progression
    disease$`critical:progress[2]` <- 1
    disease$`critical:progress[3]` <- 1 - exp(-(1 / input$ptC * (input$hospital_time - 1)))
    
    ## set up probabilities on disease scale
    disease$`.pEA` <- input$pEA
    disease$`.pIH` <- input$pIH
    disease$`.pIR` <- (1 - input$pIH) * input$pIRprime
    disease$`.pHC` <- input$pHC
    disease$`.pHR` <- (1 - input$pHC) * input$pHRprime
    disease$`.pCR` <- input$pCR
    
    ## set up scaling for mixing matrix
    disease$`.GP_A` <- input$scale_asymp
    
    ## round disease file (to prevent fingerprint form being too long)
    disease <- mutate_all(disease, round, digits = 6)
    
    ## finalise number of repeats
    disease$repeats <- repeats
    
    ## return disease file
    disease
}
