function toggleSearchBox() {
    var searchContainer = document.getElementById("search_by_title");
    if (searchContainer.style.display === "none") {
        searchContainer.style.display = "block";
    } else {
        searchContainer.style.display = "none";
    }
}

function searchByTitle() {
    var title = document.getElementById("title-input").value;

    $.ajax({
        type: "POST",
        url: "/search_by_title",
        data: { title: title },
        success: function (data) {
            displaySearchResults(data);
        }
    });
}

function displaySearchResults(data) {
    var searchResultsDiv = document.getElementById("search-results");
    searchResultsDiv.innerHTML = data;
}
