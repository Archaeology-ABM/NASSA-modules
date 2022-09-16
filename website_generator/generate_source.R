library(magrittr)
#library(kableExtra)
library(DT)

repo_path <- ".."

#### nassa input ####

nassa_yml_paths <- list.files(
  path = repo_path,
  pattern = "NASSA.yml",
  recursive = T,
  full.names = T  
)

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
libraryVersion = "v0.0.0" # TO-DO: get current NASSA-modules version (main)

#### render website from .Rmd files

rmarkdown::render_site(input = "website_source", envir = parent.frame())
