
import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000",
});

export const uploadPaper = async (file) => {
  const formData = new FormData();

  formData.append("file", file);

  const response = await API.post(
    "/papers/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }
  );

  return response.data;
};


export const askQuestion = async (query) => {

  const response = await API.post(
    "/research/ask",
    {
      query,
    }
  );

  return response.data;
};


export default API;