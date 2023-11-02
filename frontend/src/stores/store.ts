import { configureStore } from "@reduxjs/toolkit";
import testReducer from "../features/tracks/stores/testSlice";

export default configureStore({
  reducer: {
    test: testReducer,
  },
});
