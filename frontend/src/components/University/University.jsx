import { useParams } from "react-router-dom";
import UniversityGroup from "./UniversityPage";

const UniversityPage = () => {
  const { universityName } = useParams(); // 👈 this pulls `universityName` from the URL

  return <UniversityGroup universityName={universityName} />;
};

export default UniversityPage;
