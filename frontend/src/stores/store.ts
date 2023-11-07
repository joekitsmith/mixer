import { configureStore } from "@reduxjs/toolkit";
import testReducer from "../features/mixer/stores/testSlice";

export default configureStore({
  reducer: {
    test: testReducer,
  },
});
