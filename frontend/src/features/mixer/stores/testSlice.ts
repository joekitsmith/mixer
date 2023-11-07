import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { TestPayload } from "../types";

interface TestState {
  test: string;
}

const initialState: TestState = {
  test: "",
};

const testSlice = createSlice({
  name: "test",
  initialState,
  reducers: {
    testAction: (state: TestState, action: PayloadAction<TestPayload>) => {
      state.test = action.payload.test;
    },
  },
});

export default testSlice.reducer;

export const { testAction } = testSlice.actions;

export const selectTest = (state: any) => state.test.test;
