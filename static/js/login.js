sessionStorage.clear();

var loggingIn=false;

function login(){
    if(loggingIn) return;

    loggingIn=true;

    let username=document.getElementById("username").value;
    let password=document.getElementById("password").value;

    if (username=="" && password != ""){
        showMessage("Username is required!");
        loggingIn=false;
    }
    else if (username!="" && password !=""){
        fetch("user/id?username="+username+"&password="+password,{
            method:"GET"
        })
        .then(function(response){
            if (response.status === 200){
                response.json().then(function(data){
                    if(data.id==null){
                        showMessage("Username and Password do not match!");
                        loggingIn=false;
                    }
                    else{
                        sessionStorage.setItem("id",data.id)
                        sessionStorage.setItem("password",password)
                        window.location.href="home";
                    }
                })
            }
            else{
                showMessage("Login failed, please try again!")
                loggingIn=false;
            }
        })
    }

}

function showMessage(message){
    let errorDiv=document.getElementById("error message");
    errorDiv.innerHTML=message;
    errorDiv.style.opacity="100%";
}

function hideMessage(){
    let errorDiv=document.getElementById("error message");
    errorDiv.style.opacity="0%";
}

document.addEventListener('keypress',loginIfEnter);
function loginIfEnter(e)
{
    if(e.keyCode==13) login();
}