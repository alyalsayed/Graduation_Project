import { useState, useEffect } from "react";
import { makeStyles, withStyles } from "@material-ui/core/styles";
import AppBar from "@material-ui/core/AppBar";
import Toolbar from "@material-ui/core/Toolbar";
import Typography from "@material-ui/core/Typography";
import Avatar from "@material-ui/core/Avatar";
import Container from "@material-ui/core/Container";
import React from "react";
import Card from "@material-ui/core/Card";
import CardContent from "@material-ui/core/CardContent";
import {
  Paper,
  CardActionArea,
  CardMedia,
  Grid,
  TableContainer,
  Table,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
  Button,
  CircularProgress,
} from "@material-ui/core";
import { DropzoneArea } from "material-ui-dropzone";
import { common } from "@material-ui/core/colors";
import Clear from "@material-ui/icons/Clear";
import axios from "axios";
import logo from "./logo_parking.jpg";
import image from "./bg.jpg";

const ColorButton = withStyles((theme) => ({
  root: {
    color: theme.palette.getContrastText(common.white),
    backgroundColor: common.white,
    "&:hover": {
      backgroundColor: "#ffffff7a",
    },
  },
}))(Button);

const useStyles = makeStyles((theme) => ({
  grow: { flexGrow: 1 },
  clearButton: {
    width: "-webkit-fill-available",
    borderRadius: "15px",
    padding: "15px 22px",
    color: "#000000a6",
    fontSize: "20px",
    fontWeight: 900,
  },
  media: { height: 200 },
  mainContainer: {
    backgroundImage: `url(${image})`,
    backgroundRepeat: "no-repeat",
    backgroundPosition: "center",
    backgroundSize: "cover",
    height: "93vh",
    marginTop: "0",
    overflow: "hidden",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
  },
  imageCard: {
    margin: "auto",
    maxWidth: "400px",
    height: "auto",
    backgroundColor: "transparent",
    boxShadow: "0px 9px 70px 0px rgb(0 0 0 / 30%)",
    borderRadius: "15px",
  },
  imageCardEmpty: { height: "auto" },
  tableContainer: {
    backgroundColor: "transparent",
    boxShadow: "none",
  },
  table: { backgroundColor: "transparent" },
  tableHead: { backgroundColor: "transparent" },
  tableRow: { backgroundColor: "transparent" },
  tableCell: {
    fontSize: "22px",
    backgroundColor: "transparent",
    borderColor: "transparent",
    color: "#000000a6",
    fontWeight: "bolder",
    padding: "1px 24px 1px 16px",
    textAlign: "center",
  },
  tableBody: { backgroundColor: "transparent" },
  detail: {
    backgroundColor: "white",
    display: "flex",
    justifyContent: "center",
    flexDirection: "column",
    alignItems: "center",
  },
  appbar: { background: "#3F4E4F", boxShadow: "none", color: "white" },
  loader: { color: "#be6a77 !important" },
  buttonGrid: { maxWidth: "416px", width: "100%", margin: "auto" },
}));

const loadImageBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const base64result = reader.result.split(",")[1];
      resolve(base64result);
    };
    reader.onerror = (error) => reject(error);
  });
};

const processConcatenatedText = (text) => {
  const isNumeric = (char) => /[0-9\u0660-\u0669]/.test(char);
  
  let arabicPart = "";
  let numericPart = "";
  for (let char of text) {
    if (isNumeric(char)) {
      numericPart += char;
    } else {
      arabicPart += char;
    }
  }
  arabicPart = arabicPart.split("").reverse().join("");
  return arabicPart + numericPart;
};

const CLASS_LABELS_MAPPING = {
  0: "٠", 1: "١", 2: "٢", 3: "٣", 4: "٤", 5: "٥", 6: "٦", 7: "٧",
  8: "ح", 9: "٨", 10: "٩", 11: "ط", 12: "ظ", 13: "ع", 14: "أ", 15: "ب",
  16: "ض", 17: "د", 18: "ف", 19: "غ", 20: "ه", 21: "ج", 22: "ك", 23: "خ",
  24: "ل", 25: "م", 26: "ن", 27: "ق", 28: "ر", 29: "ص", 30: "س", 31: "ش",
  32: "ت", 33: "ث", 34: "و", 35: "ي", 36: "ذ", 37: "ز"
};

export const ImageUpload = () => {
  const classes = useStyles();
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [data, setData] = useState(null);
  const [image, setImage] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  let confidence = 0;

  const sendFile = async () => {
    if (image && selectedFile) {
      try {
        const base64Image = await loadImageBase64(selectedFile);
        const res = await axios({
          method: "post",
          url: "https://detect.roboflow.com/egyptian-car-plates/13",
          params: {
            api_key: process.env.REACT_APP_ROBOFLOW_API_KEY,
          },
          data: base64Image,
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
          },
        });
        if (res.status === 200) {
          const predictions = res.data.predictions;
          if (predictions && predictions.length > 0) {
            const sortedPredictions = predictions.sort((a, b) => a.x - b.x);
            
            let concatenatedText = sortedPredictions
              .map((pred) =>
                typeof pred.class_id === "number"
                  ? CLASS_LABELS_MAPPING[pred.class_id] || ""
                  : ""
              )
              .join("");
           
            concatenatedText = processConcatenatedText(concatenatedText);
            res.data.concatenated_text = concatenatedText;
          } else {
            res.data.concatenated_text = "";
          }
          console.log(res.data);
          setData(res.data);
        }
      } catch (error) {
        console.error("Error sending file to Roboflow API:", error.message);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const clearData = () => {
    setData(null);
    setImage(false);
    setSelectedFile(null);
    setPreview(null);
  };

  useEffect(() => {
    if (!selectedFile) {
      setPreview(null);
      return;
    }
    const objectUrl = URL.createObjectURL(selectedFile);
    setPreview(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [selectedFile]);

  useEffect(() => {
    if (!preview) return;
    setIsLoading(true);
    sendFile();
  }, [preview]);

  const onSelectFile = (files) => {
    if (!files || files.length === 0) {
      setSelectedFile(null);
      setImage(false);
      setData(null);
      return;
    }
    setSelectedFile(files[0]);
    setData(null);
    setImage(true);
  };

  if (data && data.confidence) {
    confidence = (parseFloat(data.confidence) * 100).toFixed(2);
  }

  return (
    <React.Fragment>
      <AppBar position="static" className={classes.appbar}>
        <Toolbar>
          <Typography className={classes.title} variant="h6" noWrap>
            Project: Egyptian Car Plate OCR
          </Typography>
          <div className={classes.grow} />
          <Avatar src={logo} />
        </Toolbar>
      </AppBar>
      <Container maxWidth={false} className={classes.mainContainer} disableGutters>
        <Grid container direction="row" justifyContent="center" alignItems="center" spacing={2}>
          <Grid item xs={12}>
            <Card className={`${classes.imageCard} ${!image ? classes.imageCardEmpty : ""}`}>
              {image && (
                <CardActionArea>
                  <CardMedia
                    className={classes.media}
                    component="img"
                    src={preview}
                    title="Original Image"
                    style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain" }}
                  />
                </CardActionArea>
              )}
              {!image && (
                <CardContent className={classes.content}>
                  <DropzoneArea
                    acceptedFiles={["image/*"]}
                    dropzoneText={"Drag and drop an image of a car plate to process"}
                    onChange={onSelectFile}
                  />
                </CardContent>
              )}
              {data && (
                <CardContent className={classes.detail}>
                  <TableContainer component={Paper} className={classes.tableContainer}>
                    <Table className={classes.table} size="small" aria-label="simple table">
                      <TableHead className={classes.tableHead}>
                        <TableRow className={classes.tableRow}>
                          <TableCell className={classes.tableCell}>Label:</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody className={classes.tableBody}>
                        <TableRow className={classes.tableRow}>
                          <TableCell component="th" scope="row" className={classes.tableCell} dir="rtl">
                            {data.concatenated_text}
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              )}
              {isLoading && (
                <CardContent className={classes.detail}>
                  <CircularProgress color="secondary" className={classes.loader} />
                  <Typography className={classes.title} variant="h6" noWrap>
                    Processing
                  </Typography>
                </CardContent>
              )}
            </Card>
          </Grid>
          {data && (
            <Grid item className={classes.buttonGrid}>
              <ColorButton
                variant="contained"
                className={classes.clearButton}
                color="primary"
                component="span"
                size="large"
                onClick={clearData}
                startIcon={<Clear fontSize="large" />}
              >
                Clear
              </ColorButton>
            </Grid>
          )}
        </Grid>
      </Container>
    </React.Fragment>
  );
};
