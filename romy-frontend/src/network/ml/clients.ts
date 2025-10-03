import createClient from "openapi-fetch";
import type { paths } from "./generated";

const mlClient = createClient<paths>({
  baseUrl: "http://localhost:8000",
});

export default mlClient;
