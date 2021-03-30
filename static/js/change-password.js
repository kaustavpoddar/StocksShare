if(sessionStorage.getItem("id") === null || sessionStorage.getItem("password") === null) logout();
var changingPassword = false;

function changePassword() {
  if(changingPassword) return;

  changingPassword = true;
  password = document.getElementById("password").value;
  newPassword = document.getElementById("new password").value;
  confirmPassword = document.getElementById("confirm password").value;
  if (password == "" && newPassword == "" && confirmPassword == "") changingPassword = false;
  else if (password == "") {
    showMessage("Password needed", false);
    changingPassword = false;
  }
  else if (newPassword == "") {
    showMessage("new password required", false);
    changingPassword = false;
  }
  else if (confirmPassword == "") {
    showMessage("new password confirmation required", false);
    changingPassword = false;
  }
  else if (password != sessionStorage.getItem("password")) {
    showMessage("incorrect password", false);
    changingPassword = false;
  }
  else if (newPassword != confirmPassword) {
    showMessage("new passwords do not match", false);
    changingPassword = false;
  }
  else if (password == newPassword) {
    showMessage("new password cannot be the same as the current one", false);
    changingPassword = false;
  }
  else if (newPassword.length < 8) {
    showMessage("password must be at least 8 characters", false);
    changingPassword = false;
  }
  else if (newPassword.length > 50) {
    showMessage("password cannot be more than 50 characters", false);
    changingPassword = false;
  }

  // send api request to update password
  else {
    showMessage("updating...", true);
    fetch("user?id=" + sessionStorage.getItem("id")
    + "&password=" + password
    + "&newPassword=" + newPassword, {
      method: "PATCH"
    })
    .then(function (response) {
      
      if (response.status === 200){
        
        sessionStorage.setItem("password", newPassword);
        
        showMessage("update successful", true);
       
        changingPassword = false;
      }
      
      else if (response.status === 400){
       
        showMessage("invalid new password", false);
       
        changingPassword = false;
      }
      else if (response.status === 403) {
        
        showMessage("incorrect password", false);
  
        changingPassword = false;
      }
      else {
 
        showMessage("password not changed, please try again", false);
  
        changingPassword = false;
      }
    })
  }
}
function loadUserMenu() {
 
  let id = sessionStorage.getItem("id");
  let password = sessionStorage.getItem("password");


  if (id !== null && password !== null) {
    fetch("user?id=" + id + "&password=" + password, {
      method: "GET"
    })
    .then(function (response) {
    
      if (response.status === 200) {
        response.json().then(function(data) {
        
          let userButton = document.createElement("div");
          userButton.setAttribute("id", "userbutton");
          userButton.classList.add("button");
          userButton.classList.add("userbutton");
          userButton.style.width = "auto";
          userButton.style.paddingLeft = "12px";
          userButton.style.paddingRight = "12px";
          userButton.onclick = function () {
            toggleMenu();
          };
          userButton.innerHTML = data.username + "&nbsp;&nbsp;&nbsp;&#9662;";
          document.getElementById("right buttons").appendChild(userButton);

      
          let menu = document.createElement("div");
          menu.classList.add("menu");
          menu.setAttribute("id", "menu");

          let menuUserSection = document.createElement("div");
          menuUserSection.classList.add("dropdownsection");

          let menuSignedInAs = document.createElement("div");
          menuSignedInAs.style.color = "#BBBBBB";
          menuSignedInAs.style.marginLeft = "10px";
          menuSignedInAs.innerHTML = "Signed in as:";
          menuUserSection.appendChild(menuSignedInAs);

          let menuUsersName = document.createElement("div");
          menuUsersName.setAttribute("id", "name");
          menuUsersName.style.color = "white";
          menuUsersName.style.marginLeft = "10px";
          menuUsersName.style.marginTop = "10px";
          menuUsersName.innerHTML = data.firstName + " " + data.lastName;
          menuUserSection.appendChild(menuUsersName);

          menu.appendChild(menuUserSection);

          let menuPagesSection = document.createElement("div");
          menuPagesSection.classList.add("dropdownsection");

          let menuHoldings = document.createElement("div");
          menuHoldings.classList.add("dropdownclickable");
          menuHoldings.onclick = function () {
            window.location.href = "holdings";
          };
          menuHoldings.innerHTML = "Holdings";
          menuPagesSection.appendChild(menuHoldings);

          let menuLots = document.createElement("div");
          menuLots.classList.add("dropdownclickable");
          menuLots.onclick = function () {
            window.location.href = "lots";
          };
          menuLots.innerHTML = "Lots";
          menuPagesSection.appendChild(menuLots);

          let menuSells = document.createElement("div");
          menuSells.classList.add("dropdownclickable");
          menuSells.onclick = function () {
            window.location.href = "sell-lots";
          };
          menuSells.innerHTML = "Sells";
          menuPagesSection.appendChild(menuSells);

          menu.appendChild(menuPagesSection);

          let menuAccountSection = document.createElement("div");
          menuAccountSection.classList.add("dropdownsection");
          menuAccountSection.style.borderBottom = "none";

          let menuAccountSettings = document.createElement("div");
          menuAccountSettings.classList.add("dropdownclickable");
          menuAccountSettings.onclick = function () {
            window.location.href = "account-settings";
          };
          menuAccountSettings.innerHTML = "Account Settings";
          menuAccountSection.appendChild(menuAccountSettings);

          let menuLogout = document.createElement("div");
          menuLogout.classList.add("dropdownclickable");
          menuLogout.onclick = function() {
            logout();
          }
          menuLogout.innerHTML = "Log Out";
          menuAccountSection.appendChild(menuLogout);

          menu.appendChild(menuAccountSection);

          document.getElementById("body").appendChild(menu);
        })
      }

      else logout();
    })
  }
  else logout();
}


function showMessage(message, success) {

  let errorDiv = document.getElementById("error message");

  if (success) errorDiv.style.color = "#24A292";
  else errorDiv.style.color = "#FF3200";

  errorDiv.innerHTML = message;
  errorDiv.style.opacity = "100%";
}

function hideMessage() {
  let errorDiv = document.getElementById("error message");
  errorDiv.style.opacity = "0%";
}
document.addEventListener('keypress', changePasswordIfEnter);
function changePasswordIfEnter(e) {
  if(e.keyCode == 13) changePassword();
}


function toggleMenu() {
  document.getElementById("menu").classList.toggle("showmenu");
}

window.onclick = function(e) {
  if (!e.target.matches(".userbutton")) {
  var myDropdown = document.getElementById("menu");
    if (myDropdown.classList.contains("showmenu")) {
      myDropdown.classList.remove("showmenu");
    }
  }
}
function logout() {
  sessionStorage.clear();
  window.location.href = "home";
}
