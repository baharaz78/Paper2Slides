import fs from "node:fs";
import path from "node:path";

import pptxgen from "pptxgenjs";

const allowedImageExtensions = new Set([
  ".png",
  ".jpg",
  ".jpeg",
]);

const planPath = process.argv[2];
const outputPath = process.argv[3];

if (!planPath || !outputPath) {
  throw new Error(
    "Usage: node renderer/render_presentation.mjs <plan.json> <output.pptx>",
  );
}

const presentationPlan = JSON.parse(
  fs.readFileSync(planPath, "utf8"),
);

const pptx = new pptxgen();

pptx.layout = "LAYOUT_WIDE";
pptx.author = "Paper2Slides";
pptx.subject = "Academic paper presentation";
pptx.title = presentationPlan.presentation_title;
pptx.company = "Paper2Slides";

function getVerifiedImagePath(imagePath) {
  if (!imagePath) {
    return null;
  }

  const resolvedPath = path.resolve(
    process.cwd(),
    imagePath,
  );

  const extension = path.extname(resolvedPath).toLowerCase();

  const isAllowed = allowedImageExtensions.has(extension);
  const exists = fs.existsSync(resolvedPath);

  if (!isAllowed || !exists) {
    return null;
  }

  return resolvedPath;
}

function addSlide(slideData, slideNumber, totalSlides) {
  const slide = pptx.addSlide();

  slide.background = {
    color: "F8FAFC",
  };

  const verifiedImagePath = getVerifiedImagePath(
    slideData.image_path,
  );

  const hasImage = verifiedImagePath !== null;

  if (hasImage) {
    console.log(
      `Slide ${slideNumber}: using image ${verifiedImagePath}`,
    );
  } else {
    console.log(
      `Slide ${slideNumber}: no approved image selected.`,
    );
  }

  const textWidth = hasImage ? 5.4 : 11.8;

  slide.addText(
    slideData.title,
    {
      x: 0.7,
      y: 0.45,
      w: 11.9,
      h: 0.5,
      fontFace: "Arial",
      fontSize: 25,
      bold: true,
      color: "102A43",
      align: "right",
      margin: 0,
      fit: "shrink",
    },
  );

  slide.addText(
    slideData.key_message,
    {
      x: 0.7,
      y: 1.2,
      w: textWidth,
      h: 0.7,
      fontFace: "Arial",
      fontSize: 18,
      bold: true,
      color: "1D4ED8",
      align: "right",
      margin: 0,
      fit: "shrink",
    },
  );

  const bulletText = slideData.bullets
    .map((bullet) => `• ${bullet}`)
    .join("\n\n");

  slide.addText(
    bulletText,
    {
      x: 0.7,
      y: 2.1,
      w: textWidth,
      h: 3.7,
      fontFace: "Arial",
      fontSize: 16,
      color: "1F2937",
      align: "right",
      breakLine: false,
      margin: 0.05,
      valign: "top",
      fit: "shrink",
    },
  );

  if (hasImage) {
    slide.addImage(
      {
        path: verifiedImagePath,
        x: 6.6,
        y: 1.6,
        w: 5.9,
        h: 3.8,
      },
    );

    slide.addText(
      slideData.image_explanation,
      {
        x: 6.6,
        y: 5.65,
        w: 5.9,
        h: 0.7,
        fontFace: "Arial",
        fontSize: 12,
        color: "475569",
        align: "right",
        margin: 0,
        fit: "shrink",
      },
    );
  }

  slide.addText(
    `${slideNumber} / ${totalSlides}`,
    {
      x: 11.55,
      y: 6.9,
      w: 0.7,
      h: 0.2,
      fontFace: "Arial",
      fontSize: 9,
      color: "64748B",
      align: "right",
      margin: 0,
    },
  );
}

const slides = presentationPlan.slides;

for (const [index, slideData] of slides.entries()) {
  addSlide(
    slideData,
    index + 1,
    slides.length,
  );
}

fs.mkdirSync(
  path.dirname(outputPath),
  {
    recursive: true,
  },
);

await pptx.writeFile(
  {
    fileName: outputPath,
  },
);

console.log(`Presentation created: ${outputPath}`);