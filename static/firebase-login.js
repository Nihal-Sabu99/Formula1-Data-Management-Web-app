'use strict';
import {initializeApp} from "https://www.gstatic.com/firebasejs/11.3.1/firebase-app.js";
import {getAuth,createUserWithEmailAndPassword,signInWithEmailAndPassword,signOut} from "https://www.gstatic.com/firebasejs/11.3.1/firebase-auth.js";

const firebaseConfig = {
    apiKey: "",
    authDomain: "",
    projectId: "",
    storageBucket: "",
    messagingSenderId: "",
    appId: ""
    };

window.addEventListener("load",function(){
    const app=initializeApp(firebaseConfig);
    const auth=getAuth(app);
    updateUI(document.cookie);
    console.log("hello world load");

    // function for signup
    document.getElementById("sign-up").addEventListener('click',function(){
        const email=document.getElementById("email").value;
        const password=document.getElementById("password").value;

        createUserWithEmailAndPassword(auth,email,password)
            .then((userCredential)=>{
                const user=userCredential.user;
                user.getIdToken().then((token)=>{
                    document.cookie="token="+token+";path=/;SameSite=Strict";
                    window.location="/";
                });
            })
            .catch((error)=>{
                console.log(error.code + " " + error.message);
            });
    });

    // function for login
    document.getElementById("login").addEventListener('click',function(){
        const email=document.getElementById("email").value;
        const password=document.getElementById("password").value;

        signInWithEmailAndPassword(auth,email,password)
            .then((userCredential)=>{
                const user = userCredential.user;
                console.log("logged in");
                user.getIdToken().then((token)=>{
                    document.cookie="token="+ token+";path=/;SameSite=Strict";
                    window.location="/";
                });
            })
            .catch((error)=>{
                console.log(error.code+" "+error.message);
            });
    });

    // function for sign out
    document.getElementById("sign-out").addEventListener('click',function(){
        signOut(auth)
            .then(()=>{
                document.cookie="token=;path=/;SameSite=Strict";
                window.location="/";
            })
            .catch((error)=>{
                console.log(error.code+" "+error.message);
            });
    });
});

// update based on authentication
function updateUI(cookie) {
    var token=parseCookieToken(cookie);
    if (token.length>0) {
        document.getElementById("login-box").hidden=true;
        document.getElementById("sign-out").hidden=false;
    } else {
        document.getElementById("login-box").hidden=false;
        document.getElementById("sign-out").hidden=true;
    }
}

// Parse authentication token from cookie
function parseCookieToken(cookie){
    var strings=cookie.split(';');
    for (let i=0;i<strings.length;i++) {
        var temp=strings[i].trim().split('=');
        if (temp[0]==="token") {
            return temp[1];
        }
    }
    return "";
}

