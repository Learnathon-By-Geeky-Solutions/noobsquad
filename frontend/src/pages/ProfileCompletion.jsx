import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import "../assets/profileCompletion.css";

const API_URL = import.meta.env.VITE_API_URL;
const availableInterests = [
  "Machine Learning", "Web Development", "Data Science", "Blockchain", "AI Ethics",
  "Cybersecurity", "Embedded Systems", "Networking", "Cloud Computing", "Quantum Computing"
];

const ProfileCompletion = () => {
  const { login } = useAuth();
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    university: "",
    department: "",
    interests: [],
    profilePicture: null,
  });
  const [errors, setErrors] = useState({
    university: false,
    department: false,
    interests: false,
  });
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const toggleInterest = (interest) => {
    setFormData((prev) => {
      const selected = prev.interests.includes(interest)
        ? prev.interests.filter((i) => i !== interest)
        : [...prev.interests, interest];
      return { ...prev, interests: selected };
    });
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];

  // List of allowed image MIME types
    const allowedTypes = [
      "image/jpeg",   // .jpg, .jpeg
      "image/png",    // .png
      "image/tiff",    // .gif
      "image/webp",   // .webp
      "image/bmp",    // .bmp
      "image/svg+xml" // .svg (Scalable Vector Graphics)
    ];

    if (file) {
      // Check if the file is an image
      if (!allowedTypes.includes(file.type)) {
        alert("Please upload a valid image file (jpg, jpeg, png, tiff, webp, bmp, svg).");
        return; // Exit early if the file is not an image
      }
      setFormData({ ...formData, profilePicture: file });

      const reader = new FileReader();
      reader.onload = () => {
        setFormData((prev) => ({ ...prev, imagePreview: reader.result }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleNext = async () => {
    const newErrors = {
      university: !formData.university,
      department: !formData.department,
      interests: formData.interests.length === 0,
    };
    setErrors(newErrors);

    if (Object.values(newErrors).includes(true)) return;
    const formDataToSend = new FormData();
    formDataToSend.append("university_name", formData.university);
    formDataToSend.append("department", formData.department);
    formData.interests.forEach((interest) =>
      formDataToSend.append("fields_of_interest", interest)
    );
    try {
      const response = await fetch(`${API_URL}/profile/step1`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        body: formDataToSend,
      });

      if (response.ok) {
        setStep(2);
      } else {
        console.error("Error submitting step 1");
      }
    } catch (error) {
      console.error("Error submitting step 1:", error);
    }
  };

  const generateAvatarImage = (initial) => {
    return new Promise((resolve) => {
      const canvas = document.createElement("canvas");
      canvas.width = 100;
      canvas.height = 100;
      const ctx = canvas.getContext("2d");
  
      // Background color (based on first letter)
      const colors = ["#F87171", "#34D399", "#60A5FA", "#FBBF24", "#A78BFA"];
      const bgColor = colors[initial.charCodeAt(0) % colors.length];
      ctx.fillStyle = bgColor;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
  
      // Text (initial of username)
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 50px Arial";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(initial, canvas.width / 2, canvas.height / 2);
  
      // Convert canvas to Blob (for file upload)
      canvas.toBlob((blob) => resolve(blob), "image/png");
    });
  };

  const handleSkip = async () => {
    const username = localStorage.getItem("username");
    console.log(username)
    // Generate the default avatar image (based on the username's first letter)
    const initial = username.charAt(0).toUpperCase();
    const avatarBlob = await generateAvatarImage(initial);  // Generate the avatar
  
    const fakeFile = new File([avatarBlob], "avatar.png", { type: "image/png" });
  
    const formDataToSend = new FormData();
    formDataToSend.append("file", fakeFile);
  
    // Send to backend as if it was a regular uploaded file
    try {
      const response = await fetch(`${API_URL}/profile/upload_picture`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`
        },
        body: formDataToSend,
      });
  
      if (response.ok) {
        login(localStorage.getItem("token"));
        navigate("/dashboard");
      } else {
        console.error("Profile picture upload failed");
      }
    } catch (error) {
      console.error("Error submitting profile picture:", error);
    }
  };

  const handleSubmit = async () => {
    if (!formData.profilePicture) {
      handleSkip();
      return;
    }
    login(localStorage.getItem("token"));
    navigate("/dashboard");

    const formDataToSend = new FormData();
      formDataToSend.append("file", formData.profilePicture);

    try {
      const response = await fetch(`${API_URL}/profile/upload_picture`, {
        method: "POST",
        headers: { 
          Authorization: `Bearer ${localStorage.getItem("token")}` 
        },
        body: formDataToSend,
      });

      if (response.ok) {
        login(localStorage.getItem("token"));
        navigate("/dashboard");
      } else {
        console.error("Profile picture upload failed");
      }
    } catch (error) {
      console.error("Error submitting profile picture:", error);
    }
  };

  return(
    <div className="profile-container">
      <h2 className="main-title">Create Your Academic Persona</h2>
      {step === 1 && (
        <div className="profile-step">
          <h3 className="step-title">Step 1: Basic Information</h3>
          <input type="text" name="university" placeholder="University Name" value={formData.university} onChange={handleChange} className={`input-box ${errors.university ? "error" : ""}`} />
          <input type="text" name="department" placeholder="Department" value={formData.department} onChange={handleChange} className={`input-box ${errors.department ? "error" : ""}`} />
          <h3 className={`interest-title ${errors.interests ? "error-text" : ""}`}>Select Fields of Interest</h3>
          <div className="interest-box">
            {availableInterests.map((interest) => (
            <button 
              key={interest}
              type="button"
              className={`chip ${formData.interests.includes(interest) ? "selected" : ""} ${errors.interests ? "error" : ""}`} 
              onClick={() => toggleInterest(interest)}
            >
              {interest}
            </button>
            ))}
          </div>
          <button onClick={handleNext} className="btn-primary">Next</button>
        </div>
      )}

      {step === 2 && (
        <div className="profile-step">
          <h3 className="step-title">Step 2: Upload Profile Picture (Optional)</h3>
          <label className="upload-box">
            {formData.profilePicture ? <img src={formData.imagePreview} alt="Preview" className="profile-preview" /> : "Drag or Drop Your Profile Picture"}
            <input type="file" name="profilePicture" onChange={handleFileChange} className="hidden" />
          </label>
          <div className="button-group">
            <button onClick={() => setStep(1)} className="btn-secondary">Back</button>
            {!formData.profilePicture ? <button onClick={handleSkip} className="btn-secondary btn-skip">Skip</button> : <button onClick={handleSubmit} className="btn-secondary btn-finish">Finish</button>}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfileCompletion;
