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

#### create index.Rmd file ####

write(c(
  "---",
  #"title: NASSA modules",
  "---",
  "",
  "<table class='pageHeader'><tr><td><h1 class='pageTitle'>Module library</h1></td><td style='text-align:right;'><img src='images/NASSA-logo.png' width='300px' alt='NASSA-logo'></td></tr></table>",
  # TO-DO: add text print of the current release version tag and date of last update
  # TD approach:
  "```{r, echo=FALSE}
    options(DT.options = list(
      pageLength = 25, 
      language = list(search = 'Search by ID or Title:'), 
      initComplete = JS(
        \"function(settings, json) {\",
        \"$(this.api().table().header()).css({'background-color': '#03989e'});\",
        \"}\"
      ),
      columnDefs = list(list(targets = c(2, 3), orderable = FALSE), list(targets = c(2, 3), searchable = FALSE))
    ))
    
    DT::datatable(nassa_table[, c('id', 'title', 'moduleVersion', 'View')], 
                  rownames = FALSE,
                  escape = FALSE,
                  colnames = c('ID', 'Title', 'Current version', '')) %>% 
      DT::formatStyle('id', fontWeight = 'bold', width = '200px') %>% 
        DT::formatStyle(c('moduleVersion', 'View'), textAlign = 'center') %>% 
          DT::formatStyle(0, target = 'row', 
            fontStyle = styleRow(1, 'italic'), 
            color = styleRow(1, 'grey'))
  ```"
  # kable approach:
  # knitr::kable(nassa_table[, c("id", "title", "moduleVersion",   "View")],
  #              col.names =   c("ID", "Title", "Current version", ""),
  #              align =       c('l',  'l',     'c',               'c'),
  #              format = "html",
  #              table.attr = "class=\'moduleList\'"
  # ) %>% kableExtra::kable_styling() %>% kableExtra::column_spec(
  #   # style specific for the ID column
  #   column = 1, 
  #   width = '200px', 
  #   bold = TRUE,
  #   border_right = TRUE
  # ) %>% kableExtra::row_spec(
  #   # style specific for TEMPLATE module rows
  #   row = c(1), # add more row numbers when adding new templates to the library. TO-DO: possibly code an automatic filter
  #   color = 'grey',
  #   italic = TRUE
  #) %>% as.character()
),
file = file.path("website_source", "index.Rmd")
)

#### render website from .Rmd files

rmarkdown::render_site(input = "website_source")
