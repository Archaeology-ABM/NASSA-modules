# Reference evapotranspiration based on FAO-56 Penman-Monteith method

*by Andreas Angourakis* (NASSA submission :rocket:)

Calculate a daily value of reference evapotranspiration, useful for vegetation (incl. crop) models. The module code is based on FAO-56 Penman-Monteith method. The implementation is based on several sources (see moduleReferences), but particularly useful was the Evapotranspiration R package (<a href='https://cran.r-project.org/web/packages/Evapotranspiration/index.html' target='_blank'>Guo et al. 2016, 2022 (v1.16)</a>). Note: values of `C_n` and `C_d` are fixed for using the grass cover reference (900 and 0.34); values for the alfalfa reference are 1600 and 0.38.

## License

**MIT**

## References

Allen, R. G., Pereira, L. S., Raes, D., & Smith, M. (1998). Crop Evapotranspiration—FAO Irrigation and Drainage Paper No. 56 (Issue March). FAO. [http://www.fao.org/3/X0490E/x0490e00.htm](http://www.fao.org/3/X0490E/x0490e00.htm)

Suleiman, A. A., & Hoogenboom, G. (2007). Comparison of Priestley-Taylor and FAO-56 Penman-Monteith for Daily Reference Evapotranspiration Estimation in Georgia. Journal of Irrigation and Drainage Engineering, 133(2), 175–182. [https://doi.org/10.1061/(ASCE)0733-9437(2007)133:2(175)](https://doi.org/10.1061/(ASCE)0733-9437(2007)133:2(175))

Jia, X. (2013). Comparison of Reference Evapotranspiration Calculations for Southeastern North Dakota. Irrigation & Drainage Systems Engineering, 2(3). [https://doi.org/10.4172/2168-9768.1000112](https://doi.org/10.4172/2168-9768.1000112)

Guo, D., Westra, S., & Maier, H. R. (2016). An R package for modelling actual, potential and reference evapotranspiration. Environmental Modelling and Software, 78, 216–224. [https://doi.org/10.1016/j.envsoft.2015.12.019](https://doi.org/10.1016/j.envsoft.2015.12.019)

Guo, D., Westra, S., & Peterson, T. (2022). Evapotranspiration: Modelling Actual, Potential and Reference Crop Evapotranspiration (1.16). [https://CRAN.R-project.org/package=Evapotranspiration](https://CRAN.R-project.org/package=Evapotranspiration)

## Further information

![Interface screenshot](netlogo_implementation/documentation/referenceEvapotranspiration%20interface.png)

See full list of documentation resources in [`documentation`](documentation/tableOfContents.md).
