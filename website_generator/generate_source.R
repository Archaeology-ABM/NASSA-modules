library(magrittr)
#library(kableExtra)
library(DT)
library(git2r)

repo_path <- ".."

#### nassa input ####

nassa_yml_paths <- list.files(
  path = repo_path,
  pattern = "NASSA.yml",
  recursive = T,
  full.names = T  
)

badge_series <- function(x, type = 'badgeDefault') {
  if (length(x) > 0) {
    prefix <- paste0('<span class="badge" id="',  type, '">')
    return(paste(prefix, x, '</span>', collapse = '&nbsp;'))
  } else {
    return('')
  }
}

nassa_table <- purrr::map_dfr(
  nassa_yml_paths,
  function(nassa_yml_path) {
    nassa_yml <- yaml::read_yaml(nassa_yml_path)
    tibble::tibble(
      path = basename(dirname(nassa_yml_path)),
      id = nassa_yml$id,
      title = nassa_yml$title,
      moduleVersion = nassa_yml$moduleVersion,
      #contributors = paste(nassa_yml$contributors, collapse = ', '), # use this structure to print out nested yml fields
      domainKeywords = paste(badge_series(nassa_yml$domainKeywords$regions, type = 'badgeRegions'),
                             badge_series(nassa_yml$domainKeywords$periods, type = 'badgePeriods'),
                             badge_series(nassa_yml$domainKeywords$subjects, type = 'badgeSubjects'),
                             collapse = '&nbsp;'),
      modellingKeywords = badge_series(nassa_yml$modellingKeywords, type = 'badgeModelling'),
      programmingKeywords = badge_series(nassa_yml$programmingKeywords, type = 'badgeProgramming'),
      `View` = paste0("<a href=\"", path, ".html\">View</a>"),
    )
  }
)

#### prepare package-wise .Rmd files ####

generate_Rmd <- function(x) {
  out_path <- file.path("website_source", paste0(x, ".Rmd"))
  template <- readLines("package_page_template.Rmd")
  template_mod <- gsub("####module_name####", x, template)
  writeLines(template_mod, con = out_path)
}
purrr::walk(nassa_table$path, generate_Rmd)

# set NASSA-modules version and current date as args when rendering site
libraryVersion = names(git2r::tags(git2r::discover_repository()))[-1]

#### copy the .bib file for each package ####

copy_bib <- function(x) {
  pac_path <- file.path(repo_path, x)
  bib_file <- list.files(pac_path, pattern = ".bib", full.names = TRUE)
  if (length(bib_file) == 1) {
    out_path <- file.path("website_source", paste0(x, ".bib"))
    file.copy(bib_file, out_path)
  }
}
purrr::walk(nassa_table$path, copy_bib)

#### render website from .Rmd files

rmarkdown::render_site(input = "website_source", envir = parent.frame())
