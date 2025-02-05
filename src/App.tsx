import { Routes, Route } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { SignUp } from "@/components/SignUp";
import { SignIn } from "@/components/SignIn";
import { Home } from "@/components/Home";
import { About } from "@/components/About";
import { UnderConstruction } from "@/components/UnderConstruction";
import { ComingSoon } from "./components/ComingSoon";

function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/about" element={<About />} />
        <Route path="/coming-soon" element={<ComingSoon />} />
        <Route path="*" element={<UnderConstruction />} />
      </Routes>
      <Footer />
    </>
  );
}

export default App;