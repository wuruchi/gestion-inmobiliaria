import React from "react";

const NotFound = () => {
  return (
    <div
      style={{
        textAlign: "center",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "1rem",
      }}
    >
      <h1 style={{ fontSize: "4rem" }}>404 - Not Found</h1>
      <div style={{ fontSize: "2rem" }}>
        <p>{window.location.href}</p>
        <p>Sorry, the page you are looking for does not exist.</p>
      </div>
      <img src='/img/oregon.jpeg' alt='Page not found' />
    </div>
  );
};

export default NotFound;
