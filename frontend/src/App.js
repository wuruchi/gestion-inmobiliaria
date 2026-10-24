import { HashRouter as Router, Route, Routes } from "react-router-dom";
import Header from "./components/Header";
import Footer from "./components/Footer";
import MainScreen from "./screens/MainScreen";
import SearchScreen from "./screens/SearchScreen";
import AlquilerVentaScreen from "./screens/AlquilerVentaScreen";
import ServiciosPropietariosScreen from "./screens/ServiciosPropietariosScreen";
import SobreNosotrosScreen from "./screens/SobreNosotrosScreen";
import Producto from "./screens/ProductoScreen";
import NotFound from "./components/NotFound";

function App() {
  return (
    <Router>
      <Header />
      <Routes>
        <Route exact path='/' element={<MainScreen />} />
        <Route exact path='/producto/:id' element={<Producto />} />
        <Route
          path='/pisos-de-alquiler-y-venta/alquiler-temporal-barcelona'
          element={<SearchScreen />}
        />
        <Route
          path='/pisos-de-alquiler-y-venta/alquiler-larga-estancia-barcelona'
          element={<SearchScreen />}
        />
        <Route
          path='/pisos-de-alquiler-y-venta/venta-de-inmuebles'
          element={<SearchScreen />}
        />
        <Route
          path='/pisos-de-alquiler-y-venta'
          element={<AlquilerVentaScreen />}
        />
        <Route
          path='/servicios-propietarios'
          element={<ServiciosPropietariosScreen />}
        />
        <Route path='/sobre-nosotros' element={<SobreNosotrosScreen />} />
        <Route path='*' element={<NotFound />} />
      </Routes>
      <Footer />
    </Router>
  );
}

export default App;
