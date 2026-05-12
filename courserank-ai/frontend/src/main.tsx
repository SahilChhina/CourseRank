import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./index.css";
import Home from "./pages/Home";
import CourseReport from "./pages/CourseReport";
import CompareCourses from "./pages/CompareCourses";
import SubmitReview from "./pages/SubmitReview";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/courses/:id" element={<CourseReport />} />
        <Route path="/compare" element={<CompareCourses />} />
        <Route path="/courses/:id/review" element={<SubmitReview />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
