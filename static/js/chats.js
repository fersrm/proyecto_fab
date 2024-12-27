// Gráfico 1
const myChart = echarts.init(document.getElementById("chart2"));

const option2 = {
  tooltip: {
    trigger: "axis",
  },
  legend: {
    data: ["femenino", "masculino"],
    textStyle: {
      color: "#D3D3D3",
    },
  },
  toolbox: {
    show: true,
    feature: {
      dataView: { show: true, readOnly: false },
      magicType: { show: true, type: ["line", "bar"] },
      restore: { show: true },
      saveAsImage: { show: true },
    },
  },
  calculable: true,
  xAxis: [
    {
      type: "category",
      // prettier-ignore
      data: communes,
    },
  ],
  yAxis: [
    {
      type: "value",
    },
  ],
  series: [
    {
      name: "femenino",
      type: "bar",
      data: femaleLegalCounts,
      markPoint: {
        data: [
          { type: "max", name: "Max" },
          { type: "min", name: "Min" },
        ],
      },
    },
    {
      name: "masculino",
      type: "bar",
      data: maleLegalCounts,
      markPoint: {
        data: [
          { type: "max", name: "Max" },
          { type: "min", name: "Min" },
        ],
      },
    },
  ],
};

myChart.setOption(option2);
myChart.resize();

// Gráfico 2 país
const myChartGeo = echarts.init(document.getElementById("chartGeo"));
myChartGeo.showLoading();

let maxSum = Number.NEGATIVE_INFINITY;
let minSum = Number.POSITIVE_INFINITY;

if (mujeres.length !== hombres.length) {
  console.error(
    "Las longitudes de los arrays de mujeres y hombres no coinciden."
  );
} else {
  for (let i = 0; i < mujeres.length; i++) {
    let suma = mujeres[i] + hombres[i];

    if (suma > maxSum) {
      maxSum = suma;
    }

    if (suma < minSum) {
      minSum = suma;
    }
  }
}

fetch(rutaGeoJson)
  .then((response) => {
    if (!response.ok) {
      throw new Error("Network response was not ok " + response.statusText);
    }
    return response.json();
  })
  .then((chileJson) => {
    myChartGeo.hideLoading();
    echarts.registerMap("Chile", chileJson);

    const optionGeo = {
      title: {
        text: "Cantidad Total por Región",
        left: "right",
        textStyle: {
          color: "#D3D3D3",
        },
      },
      tooltip: {
        trigger: "item",
        showDelay: 0,
        transitionDuration: 0.2,
      },
      visualMap: {
        left: "right",
        min: minSum,
        max: maxSum,
        inRange: {
          color: [
            "#313695",
            "#4575b4",
            "#74add1",
            "#abd9e9",
            "#e0f3f8",
            "#ffffbf",
            "#fee090",
            "#fdae61",
            "#f46d43",
            "#d73027",
            "#a50026",
          ],
        },
        text: ["Alto", "Bajo"],
        textStyle: {
          color: "#D3D3D3",
        },
        calculable: true,
      },
      toolbox: {
        show: true,
        left: "left",
        top: "top",
        feature: {
          dataView: { readOnly: false },
          restore: {},
          saveAsImage: {},
        },
      },
      series: [
        {
          name: "Estimaciones total de niños",
          type: "map",
          roam: true,
          map: "Chile",
          emphasis: {
            label: {
              show: true,
            },
          },
          data: [
            { name: "Arica y Parinacota", value: mujeres[14] + hombres[14] },
            { name: "Tarapacá", value: mujeres[0] + hombres[0] },
            { name: "Antofagasta", value: mujeres[1] + hombres[1] },
            { name: "Atacama", value: mujeres[2] + hombres[2] },
            { name: "Coquimbo", value: mujeres[3] + hombres[3] },
            { name: "Valparaíso", value: mujeres[4] + hombres[4] },
            {
              name: "Metropolitana de Santiago",
              value: mujeres[12] + hombres[12],
            },
            {
              name: "Libertador General Bernardo O’Higgins",
              value: mujeres[5] + hombres[5],
            },
            { name: "Maule", value: mujeres[6] + hombres[6] },
            { name: "Ñuble", value: mujeres[15] + hombres[15] },
            { name: "Biobío", value: mujeres[7] + hombres[7] },
            { name: "La Araucanía", value: mujeres[8] + hombres[8] },
            { name: "Los Ríos", value: mujeres[13] + hombres[13] },
            { name: "Los Lagos", value: mujeres[9] + hombres[9] },
            {
              name: "Aysén del General Carlos Ibáñez del Campo",
              value: mujeres[10] + hombres[10],
            },
            {
              name: "Magallanes y de la Antártica Chilena",
              value: mujeres[11] + hombres[11],
            },
          ],
        },
      ],
    };
    myChartGeo.setOption(optionGeo);
  })
  .catch((error) => {
    console.error("There was a problem with the fetch operation:", error);
  });

// Gráfico 3
const regionLabels = [
  "Región I",
  "Región II",
  "Región III",
  "Región IV",
  "Región V",
  "Región VI",
  "Región VII",
  "Región VIII",
  "Región IX",
  "Región X",
  "Región XI",
  "Región XII",
  "Región XIII",
  "Región XIV",
  "Región XV",
  "Región XVI",
];

const myChart3 = echarts.init(document.getElementById("chart3"));
const option3 = {
  tooltip: {
    trigger: "axis",
    axisPointer: {
      type: "shadow",
    },
  },
  legend: {
    data: ["femenino", "masculino"],
    textStyle: {
      color: "#D3D3D3",
    },
  },
  grid: {
    left: "3%",
    right: "4%",
    bottom: "3%",
    containLabel: true,
  },
  xAxis: {
    type: "value",
    axisLabel: {
      formatter: function (value) {
        return Math.floor(value) === value ? value : "";
      },
    },
  },
  yAxis: {
    type: "category",
    data: regionLabels,
  },
  series: [
    {
      name: "femenino",
      type: "bar",
      data: mujeres,
    },
    {
      name: "masculino",
      type: "bar",
      data: hombres,
    },
  ],
};
myChart3.setOption(option3);
myChart3.resize();
