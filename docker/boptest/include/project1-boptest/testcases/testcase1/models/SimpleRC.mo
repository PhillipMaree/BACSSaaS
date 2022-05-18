within ;
model TestCase5
  "A simple thermal R1C1 model with sinusoidal outside air temperature and a feedback controlled heater."
  Modelica.Thermal.HeatTransfer.Components.HeatCapacitor Ci(C = 1e5, T(displayUnit = "K", fixed = true))
    "Thermal capacitance of interior"    annotation (Placement(visible = true, transformation(extent = {{40, 0}, {60, 20}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Components.ThermalResistor Rea(R=0.01)
    "Thermal resistance to outside"
    annotation (Placement(visible = true, transformation(origin = {-40, 4.44089e-16}, extent = {{-6, -6}, {6, 6}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Sensors.TemperatureSensor senTZone
    "Room air temperature sensor"
    annotation (Placement(visible = true, transformation(origin = {74, 0}, extent = {{-6, -6}, {6, 6}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Sources.PrescribedTemperature preTOut
    "Set the outside air temperature"
    annotation (Placement(visible = true, transformation(origin = {-64, -5.55112e-16}, extent = {{-6, -6}, {6, 6}}, rotation = 0)));
  Modelica.Blocks.Sources.Sine souTOut(
    freqHz=1/(3600*24),
    offset=273.15 + 20,
    amplitude=10) "Artificial outside air temperature"
    annotation (Placement(visible = true, transformation(origin = {-94, -5.55112e-16}, extent = {{-6, -6}, {6, 6}}, rotation = 0)));
  Modelica.Blocks.Sources.Step set(
    height=2,
    offset=273.15 + 20,
    startTime=3600*24) "Room temperature sepoint"
    annotation (Placement(visible = true, transformation(origin = {-94, -30}, extent = {{-6, -6}, {6, 6}}, rotation = 0)));
  Modelica.Blocks.Continuous.LimPID con(
    controllerType=Modelica.Blocks.Types.SimpleController.P,
    k=2000,
    yMin=0,
    yMax=100000) "Feedback controller for the heater based on room temperature"
    annotation (Placement(visible = true, transformation(origin = {-64, -30}, extent = {{-6, -6}, {6, 6}}, rotation = 0)));
  Buildings.Utilities.IO.SignalExchange.Overwrite
                           oveAct(u(
      unit="W",
      min=-100000,
      max=100000), description="Heater thermal power")
                                  "Overwrite the heating power"
    annotation (Placement(visible = true, transformation(origin = {-32, -30}, extent = {{-6, -6}, {6, 6}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Sources.PrescribedHeatFlow preHeat
    "Set the heating power to the room"
    annotation (Placement(visible = true, transformation(extent = {{-10, -50}, {10, -30}}, rotation = 0)));
  Modelica.Blocks.Math.Gain eff(k=1/0.99) "Heater efficiency"
    annotation (Placement(transformation(extent={{0,-90},{20,-70}})));
  Buildings.Utilities.IO.SignalExchange.Read
                      TRooAir(                y(unit="K"),
    KPIs=Buildings.Utilities.IO.SignalExchange.SignalTypes.SignalsForKPIs.AirZoneTemperature,
    description="Zone air temperature") "Read the room air temperature"
    annotation (Placement(visible = true, transformation(origin = {64, -66}, extent = {{6, -6}, {-6, 6}}, rotation = 0)));
  Buildings.Utilities.IO.SignalExchange.Read
                      PHea(y(unit="W"),
    KPIs=Buildings.Utilities.IO.SignalExchange.SignalTypes.SignalsForKPIs.GasPower,
    description="Heater power")
                           "Read the heater power"
    annotation (Placement(transformation(extent={{80,-90},{100,-70}})));
  Modelica.Blocks.Math.Abs abs
    annotation (Placement(transformation(extent={{30,-90},{50,-70}})));
  Buildings.Utilities.IO.SignalExchange.Read
                                         CO2RooAir(
    y(unit="ppm"),
    KPIs=Buildings.Utilities.IO.SignalExchange.SignalTypes.SignalsForKPIs.CO2Concentration,
    description="Zone air CO2 concentration")
    "Read the room air CO2 concentration"
    annotation (Placement(visible = true, transformation(origin = {79, 57}, extent = {{-7, -7}, {7, 7}}, rotation = 0)));

  Modelica.Blocks.Sources.Sine     conCO2(
    amplitude=250,
    freqHz=1/(3600*24),
    offset=750) "Concetration of CO2"
    annotation (Placement(visible = true, transformation(origin = {47, 57}, extent = {{-7, -7}, {7, 7}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Components.HeatCapacitor Ce(C = 1e6, T(displayUnit = "K", fixed = true)) "Thermal capacitance of envelope" annotation(
    Placement(visible = true, transformation(extent = {{-32, 0}, {-12, 20}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Components.ThermalResistor Rie(R = 0.001) annotation(
    Placement(visible = true, transformation(origin = {6, 4.44089e-16}, extent = {{-6, -6}, {6, 6}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Components.HeatCapacitor Ch(C = 1e4, T(displayUnit = "K", fixed = true, start=298.15)) "Thermal capacitance of heater" annotation(
    Placement(visible = true, transformation(extent = {{20, -40}, {40, -20}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Components.ThermalResistor Rih(R = 0.001) "Thermal resistance between heater and interior" annotation(
    Placement(visible = true, transformation(origin = {50, -22}, extent = {{-6, -6}, {6, 6}}, rotation = -90)));
  Modelica.Thermal.HeatTransfer.Components.ThermalResistor Ria(R = 0.1) annotation(
    Placement(visible = true, transformation(origin = {4, 32}, extent = {{6, -6}, {-6, 6}}, rotation = 0)));
  inner Modelica.Blocks.Noise.GlobalSeed globalSeed annotation(
    Placement(visible = true, transformation(origin = {-80, 84}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
equation
  connect(preTOut.port, Rea.port_a) annotation(
    Line(points = {{-58, 0}, {-46, 0}}, color = {191, 0, 0}));
  connect(souTOut.y, preTOut.T) annotation(
    Line(points = {{-87, 0}, {-71, 0}}, color = {0, 0, 127}));
  connect(con.y, oveAct.u) annotation(
    Line(points = {{-57, -30}, {-39, -30}}, color = {0, 0, 127}));
  connect(oveAct.y, preHeat.Q_flow) annotation(
    Line(points = {{-25, -30}, {-13.5, -30}, {-13.5, -40}, {-10, -40}}, color = {0, 0, 127}));
  connect(oveAct.y, eff.u) annotation(
    Line(points = {{-25, -30}, {-20, -30}, {-20, -80}, {-2, -80}}, color = {0, 0, 127}));
  connect(set.y, con.u_s) annotation(
    Line(points = {{-87, -30}, {-71, -30}}, color = {0, 0, 127}));
  connect(senTZone.T, TRooAir.u) annotation(
    Line(points = {{80, 0}, {90, 0}, {90, -66}, {71, -66}}, color = {0, 0, 127}));
  connect(TRooAir.y, con.u_m) annotation(
    Line(points = {{57, -66}, {-64, -66}, {-64, -37}}, color = {0, 0, 127}));
  connect(eff.y, abs.u) annotation(
    Line(points = {{21, -80}, {28, -80}}, color = {0, 0, 127}));
  connect(abs.y, PHea.u) annotation(
    Line(points = {{51, -80}, {78, -80}}, color = {0, 0, 127}));
  connect(conCO2.y, CO2RooAir.u) annotation(
    Line(points = {{55, 57}, {71, 57}}, color = {0, 0, 127}));
  connect(Ce.port, Rie.port_a) annotation(
    Line(points = {{-22, 0}, {0, 0}}, color = {191, 0, 0}));
  connect(Ce.port, Rea.port_b) annotation(
    Line(points = {{-22, 0}, {-34, 0}}, color = {191, 0, 0}));
  connect(preHeat.port, Ch.port) annotation(
    Line(points = {{10, -40}, {30, -40}}, color = {191, 0, 0}));
  connect(Ch.port, Rih.port_b) annotation(
    Line(points = {{30, -40}, {50, -40}, {50, -28}}, color = {191, 0, 0}));
  connect(Rih.port_a, Ci.port) annotation(
    Line(points = {{50, -16}, {50, 0}}, color = {191, 0, 0}));
  connect(Rih.port_a, Rie.port_b) annotation(
    Line(points = {{50, -16}, {22, -16}, {22, 0}, {12, 0}}, color = {191, 0, 0}));
  connect(Ci.port, Rie.port_b) annotation(
    Line(points = {{50, 0}, {12, 0}}, color = {191, 0, 0}));
  connect(senTZone.port, Ci.port) annotation(
    Line(points = {{68, 0}, {50, 0}}, color = {191, 0, 0}));
  connect(Ria.port_b, preTOut.port) annotation(
    Line(points = {{-2, 32}, {-52, 32}, {-52, 0}, {-58, 0}}, color = {191, 0, 0}));
  connect(Ria.port_a, Ci.port) annotation(
    Line(points = {{10, 32}, {66, 32}, {66, 26}, {52, 26}, {52, 0}, {50, 0}}, color = {191, 0, 0}));
  connect(Rih.port_a, Ria.port_a) annotation(
    Line(points = {{50, -16}, {84, -16}, {84, 32}, {10, 32}}, color = {191, 0, 0}));
  annotation (uses(Modelica(version="3.2.3"),
      Buildings(version="8.0.0")),
      experiment(
      StopTime=60,
      Interval=1,
      Tolerance=1e-06));
end TestCase5;
