import * as React from "react";
import { Waveform } from "../components/Waveform";
import { Tracklist } from "../components/Tracklist";
import { Controller } from "../components/Controller";
import { Grid } from "@mui/material";

export const Mixer = () => {
  return (
    <Grid container spacing={4} sx={{ height: "100vh", p: 3 }}>
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
