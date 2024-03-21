let arrows = document.querySelectorAll('.arrow');
arrows.forEach((arrow) => {
    arrow.addEventListener('click', function() {
        // Call the toggleOverview function when an arrow is clicked
        toggleOverview(arrow);
    });
});

function toggleOverview(arrow) {
    var parentElement = arrow.closest('.card');
    var overviewElement = parentElement.querySelector('.overview');
    var card_body = parentElement.querySelector('.card_body');

    isOverviewVisible = overviewElement.style.left === '50%';

    if (isOverviewVisible) {
        overviewElement.style.left = '0%';
        overviewElement.style.visibility = 'collapse';

        arrow.style.transform = 'rotate(0deg)';
        card_body.style.display = 'flex';
    }
    else {
        overviewElement.style.left = '50%';
        card_body.style.display = 'none';
        overviewElement.style.visibility = 'visible';

        arrow.style.transform = 'Rotate(-180deg)'

    }
       
        

}

document.getElementById('movieForm').addEventListener('submit', function(event) {
    var inputField = document.getElementById('movie_input').value.trim();
    if (inputField != ''){

        document.getElementById('loading').style.display = 'block'; // Show loading spinner
        if (document.getElementById('recommendations')) {
            document.getElementById('recommendations').style.display = 'none';
        }
        if (document.getElementById('notfound')) {
            document.getElementById('notfound').style.display = 'none';
        }

        console.log("Function executed.")
    } else {
        event.preventDefault()
    }

});