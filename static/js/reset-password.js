if(sessionStorage.getItem("id") === null || sessionStorage.getItem("resetCode") === null) back();
var resettingPassword = false;
function resetPassword() {
 
  if(resettingPassword) return;


  resettingPassword = true;


  let newPassword = document.getElementById("new password").value;
  let confirmPassword = document.getElementById("confirm password").value;


  if (newPassword == "") {
    showMessage("password required");
    resettingPassword = false;
  }
  else if (confirmPassword == "") {
    showMessage("password confirmation required");
    resettingPassword = false;
  }
  else {
   
    if (newPassword != confirmPassword) {
      showMessage("passwords do not match");
   
      resettingPassword = false;
    }
    else if (newPassword.length < 8) {
      showMessage("password must be at least 8 characters");

      resettingPassword = false;
    }
    else {
      fetch("user/password-reset?id=" + sessionStorage.getItem("id")
      + "&resetCode=" + sessionStorage.getItem("resetCode")
      + "&newPassword=" + newPassword, {
        method: "POST"
      })
      .then(function (response) {

        if (response.status === 200) {
          response.json().then(function(data) {
            sessionStorage.setItem("id", data.id);
            sessionStorage.setItem("password", newPassword);
            sessionStorage.removeItem("resetCode", data.id);
            window.location.href = "home";
          })
        }

        else if (response.status === 403) {

          showMessage("reset code expired, please send another one");
 
          resettingPassword = false;
        }
        else {
      
          showMessage("password not reset, please try again");

          resettingPassword = false;
        }
      })
    }
  }
}
function showMessage(message){
  let errorDiv = document.getElementById("error message");
  errorDiv.innerHTML = message;
  errorDiv.style.opacity = "100%";
}
function hideMessage(){
  let errorDiv = document.getElementById("error message");
  errorDiv.style.opacity = "0%";
}
document.addEventListener('keypress', resetPasswordIfEnter);
function resetPasswordIfEnter(e) {
  if(e.keyCode == 13) resetPassword();
}
function back() {
  sessionStorage.clear();
  window.location.href = "recover-password";
}
