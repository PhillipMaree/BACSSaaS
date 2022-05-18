within ;
model TestCase5
  "A simple thermal 3R3C model with a feedback controlled heater. Parameters based on measurements from SINTEF Office, Børrestuveien 3, here:
  ../SINTEF/Flexibility Suite - Documents/FLEXor/Envelope/Envelopes RC matrix.xlsx
  Those parameters are given as [kWh/m^2], area assumed here is 100 m^2.
  Ci, Ce, Rie, Rea from ZEB LL.
  Ch, Rih from BV3.
  
  So:
    - Ci: 0.011 kWh/m2
    - Ch: 0.0093 kWh/m^2
    - Ce: 0.041 kWh/m^2
    
    - Rie: 0.048 [K/kW]
    - Rea: 1.63 [K/kW]
    - Rih: 0.13 [K/kW]
    
    
  Changed to RC-table. SIMIEN shoe-box values (except Ch, it is ca. half of Ci)
  "
  constant Modelica.SIunits.Area area = 100 "Area of building";
  constant Modelica.SIunits.Power heatPow = 5000 "Heating Power";
  
  constant Modelica.SIunits.HeatCapacity CiSpe = 16686 "Specific heat capacity of interior [J/m^2]";
  constant Modelica.SIunits.HeatCapacity CeSpe = 122400 "Specific heat capacity of interior [J/m^2]";
  constant Modelica.SIunits.HeatCapacity ChSpe = 4000 "Specific heat capacity of interior [J/m^2]";
  
  constant Modelica.SIunits.ThermalResistance RiSpe = 0.06 "Specific heat capacity of interior [K*m^2/W]";
  constant Modelica.SIunits.ThermalResistance ReSpe = 0.57 "Specific heat capacity of interior [K*m^2/W]";
  constant Modelica.SIunits.ThermalResistance RhSpe = 0.1 "Specific heat capacity of interior [K*m^2/W]";
  
  constant Real noisePower = 0.5 "Power of measurement noise[]";
  
  Modelica.Thermal.HeatTransfer.Components.HeatCapacitor Ci(C = CiSpe*area, T(
      displayUnit="K",
      fixed=true,
      start=293.15))
    "Thermal capacitance of interior"    annotation (Placement(visible = true, transformation(extent = {{50, 0}, {70, 20}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Sensors.TemperatureSensor senTZone
    "Room air temperature sensor"
    annotation (Placement(visible = true, transformation(origin = {74, 0}, extent = {{-6, -6}, {6, 6}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Sources.PrescribedTemperature preTOut
    "Set the outside air temperature"
    annotation (Placement(visible = true, transformation(origin = {-64, -5.55112e-16}, extent = {{-6, -6}, {6, 6}}, rotation = 0)));
  Modelica.Blocks.Sources.Step set(
    height= 0,
    offset=273.15 + 22,
    startTime=0) "Room temperature sepoint"
    annotation (Placement(visible = true, transformation(origin = {-128, -22}, extent = {{-6, -6}, {6, 6}}, rotation = 0)));
  Buildings.Utilities.IO.SignalExchange.Overwrite
                           oveAct(u(
      unit="W",
      min=0,
      max=10000), description="Heater thermal power")
                                  "Overwrite the heating power"
    annotation (Placement(visible = true, transformation(origin = {-29, -39}, extent = {{-5, -5}, {5, 5}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Sources.PrescribedHeatFlow preHeat
    "Set the heating power to the room"
    annotation (Placement(visible = true, transformation(extent = {{-10, -50}, {10, -30}}, rotation = 0)));
  Modelica.Blocks.Math.Gain eff(k=1/0.99) "Heater efficiency"
    annotation (Placement(transformation(extent={{0,-90},{20,-70}})));
  Buildings.Utilities.IO.SignalExchange.Read
                      TRooAir(                y(unit="K"),
    KPIs=Buildings.Utilities.IO.SignalExchange.SignalTypes.SignalsForKPIs.AirZoneTemperature,
    description="Zone air temperature") "Read the room air temperature"
    annotation (Placement(visible = true, transformation(origin = {64, -64}, extent = {{6, -6}, {-6, 6}}, rotation = 0)));
  Buildings.Utilities.IO.SignalExchange.Read
                      PHea(y(unit="W"),
    KPIs=Buildings.Utilities.IO.SignalExchange.SignalTypes.SignalsForKPIs.GasPower,
    description="Heater power")
                           "Read the heater power"
    annotation (Placement(transformation(extent={{80,-90},{100,-70}})));
  Modelica.Blocks.Math.Abs abs
    annotation (Placement(transformation(extent={{30,-90},{50,-70}})));

  Modelica.Thermal.HeatTransfer.Components.HeatCapacitor Ce(final C = CeSpe*area, T(displayUnit = "K", start=293.15)) "Thermal capacitance of envelope" annotation (
    Placement(visible = true, transformation(extent = {{-28, 0}, {-8, 20}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Components.ThermalResistor Rie(final R = RiSpe/area) annotation (
    Placement(visible = true, transformation(origin={10,-4},    extent = {{-6, -6}, {6, 6}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Components.HeatCapacitor Ch(final C = ChSpe*area, T(displayUnit = "K", start = 298.15)) "Thermal capacitance of heater" annotation(
    Placement(visible = true, transformation(extent = {{24, -52}, {44, -32}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Components.ThermalResistor Rea(final R=ReSpe/area)
    "Thermal resistance to outside"
    annotation (Placement(visible = true, transformation(origin = {-40, -4}, extent = {{-6, -6}, {6, 6}}, rotation = 0)));
  Modelica.Thermal.HeatTransfer.Components.ThermalResistor Rih(final R = RhSpe/area) "Thermal resistance between heater and interior" annotation (
    Placement(visible = true, transformation(origin = {76, -28}, extent = {{-6, -6}, {6, 6}}, rotation = -90)));
  Buildings.BoundaryConditions.WeatherData.Bus weaBus annotation (Placement(
        visible = true,transformation(extent = {{-108, 16}, {-68, 56}}, rotation = 0), iconTransformation(extent = {{-258, 26}, {-238, 46}}, rotation = 0)));
  Modelica.Blocks.Routing.RealPassThrough Tout
    annotation (Placement(transformation(extent={{-104,-6},{-92,6}})));
  Modelica.Thermal.HeatTransfer.Components.ThermalResistor Ria(R = 0.1) annotation(
    Placement(visible = true, transformation(origin = {-22, 34}, extent = {{-6, -6}, {6, 6}}, rotation = 0)));
  Modelica.Blocks.Routing.RealPassThrough Solar annotation(
    Placement(visible = true, transformation(origin = {20, 84},extent = {{-6, -6}, {6, 6}}, rotation = -90)));
  Modelica.Thermal.HeatTransfer.Sources.PrescribedHeatFlow solar_i annotation(
    Placement(visible = true, transformation(origin = {42, 16}, extent = {{-10, -10}, {10, 10}}, rotation = -90)));
  Modelica.Blocks.Math.Gain Ai(k = 50)  annotation(
    Placement(visible = true, transformation(origin = {43, 57}, extent = {{-5, -5}, {5, 5}}, rotation = -90)));
  Modelica.Blocks.Math.Gain Ae(k = 50) annotation(
    Placement(visible = true, transformation(origin = {-3, 47}, extent = {{-5, -5}, {5, 5}}, rotation = -90)));
  Modelica.Thermal.HeatTransfer.Sources.PrescribedHeatFlow solar_e annotation(
    Placement(visible = true, transformation(origin = {0, 18}, extent = {{-10, -10}, {10, 10}}, rotation = -90)));
  Modelica.Blocks.Logical.OnOffController onOffController(bandwidth = 1.5)  annotation(
    Placement(visible = true, transformation(origin = {-98, -30}, extent = {{-6, -6}, {6, 6}}, rotation = 0)));
  Modelica.Blocks.Math.BooleanToReal booleanToReal annotation(
    Placement(visible = true, transformation(origin = {-71, -43}, extent = {{-5, -5}, {5, 5}}, rotation = 0)));
  Modelica.Blocks.Sources.Constant heatingPower(k = heatPow)  annotation(
    Placement(visible = true, transformation(origin = {-69, -25}, extent = {{-5, -5}, {5, 5}}, rotation = 0)));
  Modelica.Blocks.Math.Product product annotation(
    Placement(visible = true, transformation(origin = {-47, -39}, extent = {{-5, -5}, {5, 5}}, rotation = 0)));
  inner Modelica.Blocks.Noise.GlobalSeed globalSeed annotation(
    Placement(visible = true, transformation(origin = {-82, 74}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
  Modelica.Blocks.Noise.BandLimitedWhiteNoise w_i(samplePeriod = 10, useAutomaticLocalSeed = true, useGlobalSeed = true) annotation(
    Placement(visible = true, transformation(origin = {63, 37}, extent = {{-7, -7}, {7, 7}}, rotation = 0)));
  Modelica.Blocks.Math.Add add(k1 = noisePower)  annotation(
    Placement(visible = true, transformation(origin = {91, -45}, extent = {{-7, -7}, {7, 7}}, rotation = -90)));
  Buildings.BoundaryConditions.WeatherData.ReaderTMY3 weaDat(filNam = Modelica.Utilities.Files.loadResource("../Resources/NOR_OS_Oslo.Blindern.014920_TMYx.mos"))  annotation(
    Placement(visible = true, transformation(origin = {-130, 38}, extent = {{-10, -10}, {10, 10}}, rotation = 0)));
equation
  connect(preTOut.port, Rea.port_a) annotation(
    Line(points = {{-58, 0}, {-52, 0}, {-52, -4}, {-46, -4}}, color = {191, 0, 0}));
  connect(oveAct.y, preHeat.Q_flow) annotation(
    Line(points = {{-23.5, -39}, {-15.5, -39}, {-15.5, -40}, {-10, -40}}, color = {0, 0, 127}));
  connect(oveAct.y, eff.u) annotation(
    Line(points = {{-23.5, -39}, {-18, -39}, {-18, -82}, {-10, -82}, {-10, -80}, {-2, -80}}, color = {0, 0, 127}));
  connect(eff.y, abs.u) annotation(
    Line(points = {{21, -80}, {28, -80}}, color = {0, 0, 127}));
  connect(abs.y, PHea.u) annotation(
    Line(points = {{51, -80}, {78, -80}}, color = {0, 0, 127}));
  connect(Ce.port, Rie.port_a) annotation(
    Line(points = {{-18, 0}, {-10, 0}, {-10, -4}, {4, -4}}, color = {191, 0, 0}));
  connect(Ce.port, Rea.port_b) annotation(
    Line(points = {{-18, 0}, {-28, 0}, {-28, -4}, {-34, -4}}, color = {191, 0, 0}));
  connect(Ch.port, Rih.port_b) annotation(
    Line(points = {{34, -52}, {59, -52}, {59, -34}, {76, -34}}, color = {191, 0, 0}));
  connect(Rih.port_a, Ci.port) annotation(
    Line(points = {{76, -22}, {76, -13}, {60, -13}, {60, 0}}, color = {191, 0, 0}));
  connect(senTZone.port, Ci.port) annotation(
    Line(points = {{68, 0}, {60, 0}}, color = {191, 0, 0}));
  connect(Tout.y, preTOut.T) annotation(
    Line(points = {{-91.4, 0}, {-71.2, 0}}, color = {0, 0, 127}));
  connect(weaBus.TDryBul, Tout.u) annotation(
    Line(points = {{-88, 36}, {-66, 36}, {-66, 14}, {-114, 14}, {-114, 0}, {-105.2, 0}}, color = {255, 204, 51}, thickness = 0.5));
  connect(Ria.port_a, preTOut.port) annotation(
    Line(points = {{-28, 34}, {-50, 34}, {-50, -8.88178e-16}, {-58, -8.88178e-16}}, color = {191, 0, 0}));
  connect(weaBus.HGloHor, Solar.u) annotation(
    Line(points = {{-88, 36}, {-42, 36}, {-42, 98}, {20, 98}, {20, 91}}, color = {0, 0, 127}));
  connect(Ai.u, Solar.y) annotation(
    Line(points = {{43, 63}, {20, 63}, {20, 77}}, color = {0, 0, 127}));
  connect(Ae.u, Solar.y) annotation(
    Line(points = {{-3, 53}, {-3, 62}, {20, 62}, {20, 77}}, color = {0, 0, 127}));
  connect(Ae.y, solar_e.Q_flow) annotation(
    Line(points = {{-2, 42}, {0, 42}, {0, 28}}, color = {0, 0, 127}));
  connect(Ai.y, solar_i.Q_flow) annotation(
    Line(points = {{43, 51.5}, {43, 46}, {42, 46}, {42, 26}}, color = {0, 0, 127}));
  connect(solar_e.port, Ce.port) annotation(
    Line(points = {{0, 8}, {-6, 8}, {-6, -16}, {-18, -16}, {-18, 0}}, color = {191, 0, 0}));
  connect(solar_i.port, Ci.port) annotation(
    Line(points = {{42, 6}, {42, -8}, {60, -8}, {60, 0}}, color = {191, 0, 0}));
  connect(preHeat.port, Ch.port) annotation(
    Line(points = {{10, -40}, {20, -40}, {20, -54}, {34, -54}, {34, -52}}, color = {191, 0, 0}));
  connect(Rie.port_b, Ci.port) annotation(
    Line(points = {{16, -4}, {24, -4}, {24, 0}, {60, 0}}, color = {191, 0, 0}));
  connect(Ci.port, Ria.port_b) annotation(
    Line(points = {{60, 0}, {24, 0}, {24, 34}, {-16, 34}}, color = {191, 0, 0}));
  connect(set.y, onOffController.reference) annotation(
    Line(points = {{-121, -22}, {-115.75, -22}, {-115.75, -18}, {-110.5, -18}, {-110.5, -26}, {-105, -26}}, color = {0, 0, 127}));
  connect(TRooAir.y, onOffController.u) annotation(
    Line(points = {{57, -64}, {-14, -64}, {-14, -52}, {-116, -52}, {-116, -34}, {-105, -34}}, color = {0, 0, 127}));
  connect(onOffController.y, booleanToReal.u) annotation(
    Line(points = {{-91, -30}, {-84, -30}, {-84, -50}, {-87, -50}, {-87, -37.5}, {-77, -37.5}, {-77, -43}}, color = {255, 0, 255}));
  connect(booleanToReal.y, product.u2) annotation(
    Line(points = {{-65.5, -43}, {-53, -43}, {-53, -42}}, color = {0, 0, 127}));
  connect(heatingPower.y, product.u1) annotation(
    Line(points = {{-63.5, -25}, {-53, -25}, {-53, -36}}, color = {0, 0, 127}));
  connect(senTZone.T, add.u2) annotation(
    Line(points = {{80, 0}, {87, 0}, {87, -37}}, color = {0, 0, 127}));
  connect(add.y, TRooAir.u) annotation(
    Line(points = {{92, -52}, {94, -52}, {94, -64}, {71, -64}}, color = {0, 0, 127}));
  connect(product.y, oveAct.u) annotation(
    Line(points = {{-41.5, -39}, {-35, -39}}, color = {0, 0, 127}));
  connect(weaDat.weaBus, weaBus) annotation(
    Line(points = {{-120, 38}, {-109, 38}, {-109, 36}, {-88, 36}}, color = {255, 204, 51}, thickness = 0.5));
  connect(w_i.y, add.u1) annotation(
    Line(points = {{70, 38}, {92, 38}, {92, -36}, {96, -36}}, color = {0, 0, 127}));
  annotation (uses(Modelica(version="3.2.3"),
      Buildings(version="8.0.0")),
      experiment(
      StopTime=60,
      Interval=1,
      Tolerance=1e-06));
end TestCase5;
