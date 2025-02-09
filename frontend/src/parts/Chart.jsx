"use client";

import { useEffect, useState } from "react";
import { CartesianGrid, Line, LineChart, XAxis, YAxis } from "recharts";
import "../parts-css/Chart.css";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { Button } from "@/components/ui/button";

const API_BASE = "http://localhost:8000/bitcoin-data";

const timeframes = {
  "1 Day": 1,
  "7 Days": 7,
  "1 Month": 30,
  "1 Year": 364,
};

export default function Chart() {
  const [chartData, setChartData] = useState([]);
  const [selectedTimeframe, setSelectedTimeframe] = useState("1 Day");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchBitcoinData() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(`${API_BASE}?days=${timeframes[selectedTimeframe]}`);
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();

        if (!data.prices || !Array.isArray(data.prices)) {
          throw new Error("Invalid data format from API");
        }

        // Format timestamps based on selected timeframe
        const formattedData = data.prices.map((entry) => {
          let formattedTime;

          if (selectedTimeframe === "1 Day") {
            // Show only time for "1 Day"
            formattedTime = new Date(entry.time).toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
            });
          } else {
            // Show only date for "7 Days", "1 Month", "1 Year"
            formattedTime = new Date(entry.time).toLocaleDateString("en-US", {
              month: "short",
              day: "2-digit",
            });
          }

          return { time: formattedTime, price: entry.price };
        });

        console.log("Chart Data:", formattedData); // Debugging
        setChartData(formattedData);
      } catch (err) {
        console.error("Error fetching Bitcoin data:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchBitcoinData();
  }, [selectedTimeframe]);

  // **Dynamic Y-Axis Scaling**
  const minPrice = Math.min(...chartData.map((d) => d.price), Infinity);
  const maxPrice = Math.max(...chartData.map((d) => d.price), -Infinity);
  const yPadding = (maxPrice - minPrice) * 0.05; // 5% padding on both sides

  return (
    <Card className="card">
      <CardHeader>
        <CardTitle>Bitcoin Price Chart</CardTitle>
        <CardDescription>{selectedTimeframe} Data</CardDescription>
      </CardHeader>

      <CardContent>
        {loading ? (
          <p>Loading data...</p>
        ) : error ? (
          <p className="error">{error}</p>
        ) : (
          <ChartContainer config={{}} className="chart-container">
            <LineChart width={600} height={300} data={chartData} margin={{ left: 12, right: 12 }}>
              <CartesianGrid vertical={false} strokeDasharray="3 3" />
              <XAxis dataKey="time" tickLine={false} axisLine={false} tickMargin={8} />
              <YAxis
                domain={[minPrice - yPadding, maxPrice + yPadding]} // Dynamically adjusts range
                tickFormatter={(value) => `$${value.toFixed(2)}`}
                tickLine={false}
              />
              <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
              <Line
                dataKey="price"
                type="monotone"
                stroke="#8884d8"
                strokeWidth={2}
                dot={{ r: 2 }}
                activeDot={{ r: 3 }}
              />
            </LineChart>
          </ChartContainer>
        )}
      </CardContent>

      <CardFooter className="card-footer flex space-x-2">
        {Object.keys(timeframes).map((label) => (
          <Button
            key={label}
            onClick={() => setSelectedTimeframe(label)}
            className={selectedTimeframe === label ? "selected" : ""}
          >
            {label}
          </Button>
        ))}
      </CardFooter>
    </Card>
  );
}
