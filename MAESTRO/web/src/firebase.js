import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyD0-2gl8Vc8xcPN_b3Wy9Tk1SD3wF2Teqk",
  authDomain: "gestor-torneos-2363f.firebaseapp.com",
  projectId: "gestor-torneos-2363f",
  storageBucket: "gestor-torneos-2363f.firebasestorage.app",
  messagingSenderId: "43127180934",
  appId: "1:43127180934:web:10bb168d4479fcdf050711",
  measurementId: "G-X5FKMK2P2Y"
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);