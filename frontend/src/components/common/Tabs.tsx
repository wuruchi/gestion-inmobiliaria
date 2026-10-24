import React, { useState } from "react";

interface Tab {
  title: string;
  content: React.ReactNode;
}

interface TabsProps {
  tabs: Tab[];
}

const Tabs: React.FC<TabsProps> = ({ tabs }) => {
  const [activeIndex, setActiveIndex] = useState(0);

  const handleTabClick = (index: number) => {
    setActiveIndex(index);
  };

  return (
    <div>
      <ul className='tab__controls'>
        {tabs.map((tab, index) => (
          <li
            key={index}
            onClick={() => handleTabClick(index)}
            className={
              index === activeIndex ? "tab__control--selected" : "tab__control"
            }
          >
            {tab.title}
          </li>
        ))}
      </ul>
      <div className='tab__content'>{tabs[activeIndex].content}</div>
    </div>
  );
};

export default Tabs;
