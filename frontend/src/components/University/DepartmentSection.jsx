import { useState } from "react";
import MemberCard from "./MemoryCard";

const DepartmentSection = ({ deptName, members }) => {
  const [expanded, setExpanded] = useState(false);
  const visibleMembers = expanded ? members : members.slice(0, 4);

  return (
    <div className="mb-4 bg-gray-50 p-3 rounded-xl shadow">
      <div className="font-bold text-gray-800 mb-2">{deptName}</div>
      <div className="space-y-1">
        {visibleMembers.map((m, i) => (
          <MemberCard key={i} username={m.username} email={m.email} />
        ))}
        {members.length > 4 && (
          <button
            className="text-sm text-blue-600 hover:underline mt-1"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? "Show less" : `+${members.length - 4} more`}
          </button>
        )}
      </div>
    </div>
  );
};

export default DepartmentSection;
