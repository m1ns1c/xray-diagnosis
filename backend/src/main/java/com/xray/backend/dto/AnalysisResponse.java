package com.xray.backend.dto;

import com.xray.backend.entity.Analysis;
import lombok.Getter;
import java.time.LocalDateTime;

@Getter
public class AnalysisResponse {
    private Long id;
    private String result;
    private Double confidence;
    private String imagePath;
    private LocalDateTime createdAt;

    public AnalysisResponse(Analysis analysis) {
        this.id = analysis.getId();
        this.result = analysis.getResult();
        this.confidence = analysis.getConfidence();
        this.imagePath = analysis.getImagePath();
        this.createdAt = analysis.getCreatedAt();
    }
}