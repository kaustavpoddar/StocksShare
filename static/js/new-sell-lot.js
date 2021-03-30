if(sessionStorage.getItem("id") === null || sessionStorage.getItem("password") === null) logout();

var addingSellLot = false;


function addSellLot() {
  if(addingSellLot) return;

  addingSellLot = true;

  symbol = document.getElementById("symbol").value;
  date = document.getElementById("date").value;
  shares = document.getElementById("shares").value;
  price = document.getElementById("price").value;

  if (symbol == "" && date == "" && shares == "" && cost == "") addingSellLot = false;
  else if (symbol == "") {
    showMessage("Symbol required", false);
    addingSellLot = false;
  }
  else if (date == "") {
    showMessage("Sell date required", false);
    addingSellLot = false;
  }
  else if (shares == "") {
    showMessage("Shares required", false);
    addingSellLot = false;
  }
  else if (price == "") {
    showMessage("Price required", false);
    addingSellLot = false;
  }

  else {
    showMessage("adding...", true);
    if(price.charAt(0) == "$") price = price.substring(1);
    fetch("user/sell-lots?id=" + sessionStorage.getItem("id")
    + "&password=" + sessionStorage.getItem("password")
    + "&symbol=" + symbol
    + "&sellDate=" + date
    + "&sellPrice=" + price
    + "&shares=" + shares, {
      method: "POST"
    })
    .then(function (response) {
      if (response.status === 200) window.location.href = "sell-lots";
      else if (response.status === 400){
        response.json().then(function(data) {
          if (data.error === 20009) showMessage("invalid symbol");
          else if (data.error === 20012) showMessage("must be a valid date in the format YYYY-MM-DD");
          else if (data.error === 20010) showMessage("invalid amount of shares");
          else if (data.error === 20013) showMessage("invalid price");
          else showMessage("sell lot not added, please try again", false);
          addingSellLot = false;
        })
      }
      else if (response.status === 409){
        response.json().then(function(data) {
          let shareDescriptor = " shares ";
          if(shares == 1) shareDescriptor = " share ";
          if (data.error === 2000) showMessage("selling " + shares + shareDescriptor + "of " + symbol.toUpperCase() + " would result in more shares being sold than bought");
          else showMessage("sell lot not added, please try again", false);
          addingSellLot = false;
        })
      }
      else {
        showMessage("sell lot not added, please try again", false);
        addingSellLot = false;
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


function showMessage(message, success){
  let errorDiv = document.getElementById("error message");
  if (success) errorDiv.style.color = "#24A292";
  else errorDiv.style.color = "#FF3200";
  errorDiv.innerHTML = message;
  errorDiv.style.opacity = "100%";
}


function hideMessage(){
  let errorDiv = document.getElementById("error message");
  errorDiv.style.opacity = "0%";
}


document.addEventListener('keypress', addSellLotIfEnter);
function addSellLotIfEnter(e) {
  if(e.keyCode == 13) addSellLot();
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
