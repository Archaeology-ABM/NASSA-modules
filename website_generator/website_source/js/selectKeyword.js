$(document).ready(function() {
    // Verify the table ID by logging it
    //console.log('Table ID:', '#nassa_table_container_table');

    // DataTable instance using the correct ID
    var table = $('#nassa_table_container_table').DataTable();
    
    // Check if the table is correctly initialized
    //if (table) {
    //  console.log('DataTable initialized successfully.');
    //} else {
    //  console.log('Failed to initialize DataTable.');
    //}

    const searchInput = document.querySelector('#nassa_table_container input[type="search"]');
    //const keywordColumnIndex = 6; // Assuming "Keywords" is the 7th column (0-indexed)
    const event = new Event('input', { bubbles: true });

    // Add click event listener to each badge
    $(document).on('click', '.badge', function() {
      var keyword = $(this).data('keyword');
      //console.log('Badge clicked, keyword:', keyword); // Debugging output

      // Apply the search filter with the keyword
      if (keyword) {
        // Select the search input within the nassa_table_container
        
        //table.column(keywordColumnIndex).search("^\\b" + keyword + "\\b$", true, false, true).draw();
 
        // Check if the search input exists
        if (searchInput) {
          // Handle special case for single-character keywords like "R"
          var searchValue;
          if (keyword.length === 1) {
            searchValue = '\\b' + keyword + '\\b'; // Word boundary regex for exact match
          } else {
            searchValue = keyword;
          }
          
          // Set the value to your desired string
          if (searchInput.value.length > 0)
          {
            searchInput.value = searchInput.value + ' ' + searchValue;
          }
          else
          {
            searchInput.value = searchValue;
          }
          
          // Trigger the input event to apply the search filter immediately
          searchInput.dispatchEvent(event);
          
          //console.log('✔️ Search input value has been set successfully!');
        } else {
          //console.error('❗ Search input not found within the specified container.');
        }
      }
    });

    // Reset the search filter when 'Show All' is clicked
    $(document).on('click', '#resetFilter', function() {
      //console.log('Reset button clicked.'); // Debugging output
      searchInput.value = ''
      searchInput.dispatchEvent(event);
    });
  });
  