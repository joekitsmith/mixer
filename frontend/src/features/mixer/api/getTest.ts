import { useQuery } from "react-query";
import { axios } from "../../../lib/axios";
import { TestResponse } from "../types";

export type TestQuery = {
  test: string;
};

export const getTest = ({ test }: TestQuery): Promise<TestResponse> => {
  return axios.get(`/test`);
};

export const useTest = (testQuery: TestQuery) => {
  return useQuery({
    queryKey: ["test", ...Object.values(testQuery)],
    queryFn: () => getTest(testQuery),
    keepPreviousData: true,
  });
};
