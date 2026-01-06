import React, { createContext, useState, useContext, useEffect } from "react";

const LessonContext = createContext();

export const useLesson = () => useContext(LessonContext);

export const LessonProvider = ({ children }) => {
  const [selectedChapter, setSelectedChapter] = useState(null);
  const [lessonData, setLessonData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [includeDetails, setIncludeDetails] = useState(false);

  const selectChapter = async (title) => {
    setSelectedChapter(title);
    setLoading(true);
    setError(null);
    setLessonData(null);
    setCurrentStepIndex(0);

    try {
      const response = await fetch(
        "http://localhost:5001/api/generate-lesson",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ chapterTitle: title, includeDetails }),
        }
      );

      if (!response.ok) throw new Error("Failed to generate lesson");

      const data = await response.json();
      if (data.success) {
        setLessonData(data.steps);
      } else {
        throw new Error(data.error || "Unknown error");
      }
    } catch (err) {
      console.error("Lesson selection error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const requestCustomLesson = async (query) => {
    setSelectedChapter(query);
    setLoading(true);
    setError(null);
    setLessonData(null);
    setCurrentStepIndex(0);

    try {
      const response = await fetch(
        "http://localhost:5001/api/generate-lesson",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ userRequest: query, includeDetails }),
        }
      );

      if (!response.ok) throw new Error("Failed to generate custom lesson");

      const data = await response.json();
      if (data.success) {
        setLessonData(data.steps);
      } else {
        throw new Error(data.error || "Unknown error");
      }
    } catch (err) {
      console.error("Custom lesson request error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const nextStep = () => {
    if (lessonData && currentStepIndex < lessonData.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    }
  };

  const prevStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
    }
  };

  const resetLesson = () => {
    setSelectedChapter(null);
    setLessonData(null);
    setError(null);
    setLoading(false);
    setCurrentStepIndex(0);
  };

  const forwardStepToBlender = async (step) => {
    if (!step) return;
    try {
      await fetch("http://localhost:5001/api/mcp/forward", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lesson: [step] }),
      });
    } catch (err) {
      console.error("Failed to forward step to Blender:", err);
    }
  };

  useEffect(() => {
    if (lessonData && lessonData[currentStepIndex]) {
      forwardStepToBlender(lessonData[currentStepIndex]);
    }
  }, [lessonData, currentStepIndex]);

  return (
    <LessonContext.Provider
      value={{
        selectedChapter,
        lessonData,
        loading,
        error,
        currentStepIndex,
        includeDetails,
        setIncludeDetails,
        selectChapter,
        requestCustomLesson,
        nextStep,
        prevStep,
        resetLesson,
      }}
    >
      {children}
    </LessonContext.Provider>
  );
};
