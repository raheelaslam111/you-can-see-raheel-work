
function get_partners(){



var email = document.getElementById("email").value;
if (email !=""){


$.ajax({
            url: "/get/email",
            method: "POST",
            dataType: "json",
            data: {email:email},
            success: function (data) {
               if (data['exist']){
                alert('CPBids Username is already taken, please choose another: ' + email);
               }
            },
            error: function (error) {
                alert('error: ' + error);
            }
        });
}

}
