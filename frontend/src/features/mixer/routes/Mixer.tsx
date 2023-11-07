import * as React from "react";
import { Waveform } from "../components/Waveform";
import { Tracklist } from "../components/Tracklist";
import { Controller } from "../components/Controller";
import { Grid } from "@mui/material";

export const Mixer = () => {
  return (
    <Grid container sx={{ height: "98vh" }}>
      <Grid item xs={12}>
        <Waveform />
      </Grid>
      <Grid item xs={6}>
        <Tracklist />
      </Grid>
      <Grid item xs={6}>
        <Controller />
      </Grid>
    </Grid>
  );
};
