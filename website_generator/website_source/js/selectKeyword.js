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
    const keywordColumnIndex = 6; // Assuming "Keywords" is the 7th column (0-indexed)
    const event = new Event('input', { bubbles: true });

    // Add click event listener to each badge
    $(document).on('click', '.badge', function() {
      var keyword = $(this).data('keyword');
      //console.log('Badge clicked, keyword:', keyword); // Debugging output

      // Apply the search filter with the keyword
      if (keyword) {
        //table.columns().search(keyword).draw(); 
        // Select the search input within the nassa_table_container
        

        // Check if the search input exists
        if (searchInput) {
          // Set the value to your desired string
          if (searchInput.value.length > 0)
          {
            searchInput.value = searchInput.value + ' ' + keyword;
          }
          else
          {
            searchInput.value = keyword;
          }
          
          // Apply a custom search to the "Keywords" column
          table.column(keywordColumnIndex).search(function(data, type) {
            // Check if the data in the "Keywords" column contains the exact keyword
            const regex = new RegExp(`(^|,\\s*)${searchTerm}(,|$)`, 'i');
            return regex.test(data);
          });
          
          // Trigger the input event to apply the search filter immediately
          searchInput.dispatchEvent(event);
          
          table.draw(); // Redraw the table to apply the custom filter
          
          //console.log('✔️ Search input value has been set successfully!');
        } else {
          //console.error('❗ Search input not found within the specified container.');
        }
      }
    });

    // Optional: Add a button to reset the search filter
    //$('.legend').append('<button id="resetFilter" style="margin-left: 20px;">Show All</button>');
    // Reset the search filter when 'Show All' is clicked
    $(document).on('click', '#resetFilter', function() {
      //console.log('Reset button clicked.'); // Debugging output
      searchInput.value = ''
      searchInput.dispatchEvent(event);
      //table.search('').draw(); 
    });
  });
  