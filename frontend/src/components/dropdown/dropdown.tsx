import React, { useEffect } from "react";

type Props = {
    trigger: JSX.Element;
    menu: JSX.Element[];
};

const Dropdown = (props: Props) => {
    const [open, setOpen] = React.useState(false);
    const dropdownRef = React.useRef<HTMLDivElement>(null);
    const handleOpen = () => setOpen(!open);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (
                dropdownRef.current &&
                !dropdownRef.current.contains(event.target as Node)
            ) {
                setOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);

        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    return (
        <div className="dropdown" ref={dropdownRef}>
            {React.cloneElement(props.trigger, { onClick: handleOpen })}
            {open ? (
                <ul className="dropdown__menu">
                    {props.menu.map((item, index) => (
                        <li key={index} className="menu-item">
                            {React.cloneElement(item, {
                                onClick: () => {
                                    if (item.props.onClick) {
                                        item.props.onClick();
                                    }
                                    setOpen(false);
                                },
                            })}
                        </li>
                    ))}
                </ul>
            ) : null}
        </div>
    );
};

export default Dropdown;
