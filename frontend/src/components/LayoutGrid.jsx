import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Box, IconButton } from "@mui/material";
import { X } from "lucide-react";

export const LayoutGrid = ({ cards, columns = 3 }) => {
    const [selectedId, setSelectedId] = useState(null);

    const handleOutsideClick = () => {
        setSelectedId(null);
    };

    return (
        <Box
            sx={{
                width: "100%",
                height: "100%",
                padding: { xs: 2, md: 4 },
                display: "grid",
                gridTemplateColumns: { xs: "1fr", md: `repeat(${columns}, 1fr)` },
                gridAutoRows: "minmax(300px, auto)",
                gap: 4,
                position: "relative",
            }}
        >
            {cards.map((card, i) => {
                const isSelected = selectedId === card.id;

                return (
                    <Box
                        key={card.id || i}
                        sx={{
                            gridColumn: card.colSpan || "span 1",
                            gridRow: card.rowSpan || "span 1",
                            position: "relative",
                            minHeight: 300,
                            zIndex: isSelected ? 1000 : 1,
                        }}
                    >
                        <motion.div
                            layout
                            onClick={() => !isSelected && setSelectedId(card.id)}
                            transition={{
                                type: "spring",
                                stiffness: 260,
                                damping: 20,
                            }}
                            style={{
                                cursor: isSelected ? "default" : "pointer",
                                width: "100%",
                                height: "100%",
                                borderRadius: "8px",
                                ...(isSelected ? {
                                    position: "fixed",
                                    top: "7.5%",
                                    left: "5%",
                                    width: "90%",
                                    height: "85%",
                                    zIndex: 1001,
                                    margin: "0 auto",
                                    boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
                                } : {
                                    position: "absolute",
                                    top: 0,
                                    left: 0,
                                })
                            }}
                            whileHover={!isSelected ? { scale: 1.02 } : {}}
                            whileTap={!isSelected ? { scale: 0.98 } : {}}
                        >
                            {isSelected && (
                                <Box sx={{ position: 'absolute', top: -48, right: 0, zIndex: 1002 }}>
                                    <IconButton 
                                        onClick={(e) => { e.stopPropagation(); handleOutsideClick(); }}
                                        sx={{ 
                                            color: '#fff', 
                                            bgcolor: 'rgba(255,255,255,0.1)', 
                                            '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' } 
                                        }}
                                    >
                                        <X size={24} />
                                    </IconButton>
                                </Box>
                            )}
                            {typeof card.content === 'function' ? card.content({ isSelected }) : card.content}
                            
                            {/* Overlay for unselected cards */}
                            <AnimatePresence>
                                {!isSelected && selectedId && (
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 0.5 }}
                                        exit={{ opacity: 0 }}
                                        style={{
                                            position: "absolute",
                                            inset: 0,
                                            backgroundColor: "black",
                                            borderRadius: "inherit",
                                            zIndex: 10,
                                            pointerEvents: "none"
                                        }}
                                    />
                                )}
                            </AnimatePresence>
                        </motion.div>
                    </Box>
                );
            })}

            {/* Global Overlay Background */}
            <AnimatePresence>
                {selectedId && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        style={{
                            position: "fixed",
                            top: 0,
                            left: 0,
                            right: 0,
                            bottom: 0,
                            zIndex: 999,
                            backgroundColor: "rgba(0,0,0,0.8)",
                            backdropFilter: "blur(10px)",
                        }}
                        onClick={handleOutsideClick}
                    />
                )}
            </AnimatePresence>
        </Box>
    );
};

export default LayoutGrid;
