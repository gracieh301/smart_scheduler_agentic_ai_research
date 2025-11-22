import { useState } from "react";

function App() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setMessage("");
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a PDF file first.");
      return;
    }

    setUploading(true);
    setMessage("");

    try {
      // Replace this with your backend endpoint (n8n webhook or Flask route)
      const backendUrl = "http://localhost:5678/upload";

      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(backendUrl, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        setMessage("✅ File uploaded successfully!");
      } else {
        setMessage("❌ Upload failed. Please try again.");
      }
    } catch (error) {
      console.error(error);
      setMessage("⚠️ An error occurred while uploading.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.heading}>Smart Scheduler</h1>
      <p style={styles.text}>Upload your course syllabi (PDF format)</p>

      <input
        type="file"
        accept="application/pdf"
        onChange={handleFileChange}
        style={styles.input}
      />

      <button
        onClick={handleUpload}
        disabled={uploading}
        style={{
          ...styles.button,
          backgroundColor: uploading ? "#555" : "#1e90ff",
        }}
      >
        {uploading ? "Uploading..." : "Upload"}
      </button>

      {message && <p style={styles.message}>{message}</p>}
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    height: "100vh",
    fontFamily: "Segoe UI, sans-serif",
    backgroundColor: "#121212", // dark background
    color: "#ffffff", // white text
  },
  heading: {
    fontSize: "2.5rem",
    marginBottom: "10px",
    color: "#ffffff",
  },
  text: {
    marginBottom: "20px",
    fontSize: "1.1rem",
  },
  input: {
    marginBottom: "15px",
    color: "#ffffff",
  },
  button: {
    padding: "10px 20px",
    border: "none",
    borderRadius: "8px",
    color: "white",
    cursor: "pointer",
    fontSize: "1rem",
    transition: "0.2s",
  },
  message: {
    marginTop: "15px",
    fontWeight: "bold",
  },
};

export default App;
