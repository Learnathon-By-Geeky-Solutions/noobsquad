import { useEffect, useState } from "react";
import DepartmentSection from "./DepartmentSection";
import UniversityPostFeed from "./PostFeed";

const UniversityGroup = ({ universityName }) => {
  const [universityData, setUniversityData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUniversityInfo = async () => {
      try {
        const res = await fetch(
          `http://127.0.0.1:8000/universities/${universityName}`
        );
        const data = await res.json();
        console.log(data)
        setUniversityData(data);
      } catch (err) {
        console.error("Error fetching university data:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchUniversityInfo();
  }, [universityName]);

  if (loading) return <div className="text-center p-8">Loading...</div>;
  if (!universityData) return <div className="text-center p-8">No data found.</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 p-4 max-w-screen-xl mx-auto">
      {/* Left Sidebar - Departments */}
      <div className="md:col-span-1">
        <h2 className="text-xl font-semibold mb-2">Departments</h2>
        {Object.entries(universityData.departments).map(([dept, members]) => (
          <DepartmentSection key={dept} deptName={dept} members={members} />
        ))}
      </div>

      {/* Middle Section - Posts */}
      <div className="md:col-span-3">
        <h2 className="text-xl font-semibold mb-4">
          #{universityName.toUpperCase()} Posts
        </h2>
        <UniversityPostFeed postIds={universityData.post_ids} />
      </div>
    </div>
  );
};

export default UniversityGroup;
