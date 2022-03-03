---
title: "Random Walk in R"
output: 
  html_document:
    keep_md: true
    df_print: paged
---


Libraries required

```r
library(tidyverse)
```

```
## -- Attaching packages --------------------------------------- tidyverse 1.3.0 --
```

```
## v ggplot2 3.3.2     v purrr   0.3.4
## v tibble  3.0.4     v dplyr   1.0.2
## v tidyr   1.1.2     v stringr 1.4.0
## v readr   1.4.0     v forcats 0.5.0
```

```
## -- Conflicts ------------------------------------------ tidyverse_conflicts() --
## x dplyr::filter() masks stats::filter()
## x dplyr::lag()    masks stats::lag()
```

```r
library(ggrepel)
```

Define initial parameters of the 2D movement

```r
set.seed(6)
n<-50 #Lenght of the walk
initialX<-0.0 #initial x coordinate
initialY<-0.0 #initial y coordinate
```

Create tibble to store the trajectory

```r
steps<-1:n
X<-rep(NA,n)
Y<-rep(NA,n)
trajectory<-tibble(steps,X,Y)
```

## Method 1. Simultaneous movement in X and Y in a bidimensional grid

```r
trajectory$X<-c(initialX,initialX+cumsum(sample(c(-1,1),size = n-1,replace=TRUE)))
trajectory$Y<-c(initialY,initialY+cumsum(sample(c(-1,1),size = n-1,replace=TRUE)))
```


```r
ggplot(trajectory, aes(X,Y,label=steps))+
  geom_path()+
  geom_point()+
  geom_text_repel()+
  xlab("x coordinate") + 
  ylab("y coordinate") +
  ggtitle("Simultaeous random walk in a grid")
```

![](2D-Random-walk_files/figure-html/unnamed-chunk-5-1.png)<!-- -->


## Method 2. Sequential random movement in X and Y in a bidimensional grid

```r
aux1<-sample(c(0,1),size = n-1,replace=TRUE)
aux2<-1-aux1
trajectory$X<-c(initialX,initialX+cumsum(aux1*sample(c(-1,1),size = n-1,replace=TRUE)))
trajectory$Y<-c(initialY,initialY+cumsum(aux2*sample(c(-1,1),size = n-1,replace=TRUE)))
```



```r
ggplot(trajectory, aes(X,Y,label=steps))+
  geom_path()+
  geom_point()+
  geom_text_repel()+
  xlab("x coordinate") + 
  ylab("y coordinate") +
  ggtitle("Sequential random walk in a grid")
```

![](2D-Random-walk_files/figure-html/unnamed-chunk-7-1.png)<!-- -->

## Method 3. 2D Random walk not constrained to a grid (fixed step)

```r
stepSize<-1
aux1<-runif(n-1,min=0,max=2*pi)
aux2<-cos(aux1)*stepSize
aux3<-sin(aux1)*stepSize
trajectory$X<-c(initialX,initialX+cumsum(aux2))
trajectory$Y<-c(initialY,initialY+cumsum(aux3))
```



```r
ggplot(trajectory, aes(X,Y,label=steps))+
  geom_path()+
  geom_point()+
  geom_text_repel()+
  xlab("x coordinate") + 
  ylab("y coordinate") +
  ggtitle("2D random walk")
```

![](2D-Random-walk_files/figure-html/unnamed-chunk-9-1.png)<!-- -->
