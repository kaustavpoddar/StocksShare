sessionStorage.clear();
var sendingResetCode = false;
function sendResetCode() {
   if(sendingResetCode) return;
  sendingResetCode = true;
  email = document.getElementById("email").value;
  if (email == "") {
    showSendResetCodeMessage("email required", false);
    sendingResetCode = false;
  }
  else {
    showSendResetCodeMessage("sending...", true);
    fetch("user/password-reset?email=" + email, {
      method: "GET"
    })
    .then(function (response) {
   
      if (response.status === 200){

        showSendResetCodeMessage("email sent, code expires in 5 minutes", true);

        sendingResetCode = false;
      }

      else if (response.status === 403) {
        response.json().then(function(data) {
  
          if(data.error === 1000) showSendResetCodeMessage("no user with this email", false);
          else showSendResetCodeMessage("email not sent, please try again", false);

          sendingResetCode = false;
        })
      }
      else {
  
        showSendResetCodeMessage("email not sent, please try again", false);

        sendingResetCode = false;
      }
    })
  }
}

var resettingPassword = false;

function resetPassword() {
  if(resettingPassword) return;

  resettingPassword = true;
  username = document.getElementById("username").value;
  resetCode = document.getElementById("reset code").value;
  if (username == "" && resetCode == "") {
    showResetPasswordMessage("username and reset code required");
    resettingPassword = false;
  }
  else if (username == "") {
    showResetPasswordMessage("username required");
    resettingPassword = false;
  }
  else if (resetCode == "") {
    showResetPasswordMessage("reset code required");
    resettingPassword = false;
  }

  else{
    fetch("user/password-reset/validate?username=" + username + "&resetCode=" + resetCode, {
      method: "GET"
    })
    .then(function (response) {
      
      if (response.status === 200){
        response.json().then(function(data) {
      
          sessionStorage.setItem("id", data.id);
          sessionStorage.setItem("resetCode", resetCode);
          window.location.href = "reset-password";
        })
      }

      else if (response.status === 403) {
        response.json().then(function(data) {

          if(data.error === 1000) showResetPasswordMessage("username and reset code do not match");
          else if(data.error === 1002) showResetPasswordMessage("too many attempts, try sending another reset code");

          resettingPassword = false;
        })
      }
      else {
  
        showResetPasswordMessage("error, please try again");
        resettingPassword = false;
      }
    })
  }
}

function showSendResetCodeMessage(message, success){
  let sendResetCodeErrorDiv = document.getElementById("send reset code error message");
  if (success) sendResetCodeErrorDiv.style.color = "#24A292";
  else sendResetCodeErrorDiv.style.color = "#FF3200";
  sendResetCodeErrorDiv.innerHTML = message;
  sendResetCodeErrorDiv.style.opacity = "100%";
}
function showResetPasswordMessage(message){
  let resetPasswordErrorDiv = document.getElementById("reset password error message");
  resetPasswordErrorDiv.innerHTML = message;
  resetPasswordErrorDiv.style.opacity = "100%";
}

function hideMessages(){
  let resetPasswordErrorDiv = document.getElementById("reset password error message");
  let sendResetCodeErrorDiv = document.getElementById("send reset code error message");
  resetPasswordErrorDiv.style.opacity = "0%";
  sendResetCodeErrorDiv.style.opacity = "0%";
}
