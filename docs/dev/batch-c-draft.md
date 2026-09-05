# Materialized code — batch C: all controllers with direct handler injection

<!-- file: src/e_estoque/product/web/CategoryController.java -->
```java
package io.github.mzet97.eestoque.product.web;

import java.net.URI;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import io.github.mzet97.eestoque.product.application.CategoryViewModel;
import io.github.mzet97.eestoque.product.application.CreateCategoryCommand;
import io.github.mzet97.eestoque.product.application.CreateCategoryHandler;
import io.github.mzet97.eestoque.product.application.DeleteCategoryCommand;
import io.github.mzet97.eestoque.product.application.DeleteCategoryHandler;
import io.github.mzet97.eestoque.product.application.GetCategoryByIdHandler;
import io.github.mzet97.eestoque.product.application.GetCategoryByIdQuery;
import io.github.mzet97.eestoque.product.application.GridifyCategoriesQuery;
import io.github.mzet97.eestoque.product.application.SearchCategoriesHandler;
import io.github.mzet97.eestoque.product.application.SearchCategoriesQuery;
import io.github.mzet97.eestoque.product.application.UpdateCategoryCommand;
import io.github.mzet97.eestoque.product.application.UpdateCategoryHandler;
import io.github.mzet97.eestoque.shared.application.BaseResult;
import io.github.mzet97.eestoque.shared.application.BaseResultList;
import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/Categories")
public class CategoryController {

    private final CreateCategoryHandler createHandler;
    private final UpdateCategoryHandler updateHandler;
    private final DeleteCategoryHandler deleteHandler;
    private final GetCategoryByIdHandler getByIdHandler;
    private final SearchCategoriesHandler searchHandler;
    private final io.github.mzet97.eestoque.product.application.SearchCategoriesHandler gridifyHandler;

    public CategoryController(
            CreateCategoryHandler createHandler,
            UpdateCategoryHandler updateHandler,
            DeleteCategoryHandler deleteHandler,
            GetCategoryByIdHandler getByIdHandler,
            SearchCategoriesHandler searchHandler,
            io.github.mzet97.eestoque.product.application.SearchCategoriesHandler gridifyHandler) {
        this.createHandler = createHandler;
        this.updateHandler = updateHandler;
        this.deleteHandler = deleteHandler;
        this.getByIdHandler = getByIdHandler;
        this.searchHandler = searchHandler;
        this.gridifyHandler = io.github.mzet97.eestoque.product.application.GridifyHandlersHelper.gridifyCategories(
                searchHandler);
    }

    @GetMapping
    public BaseResultList<CategoryViewModel> search(
            @RequestParam(required = false) String name,
            @RequestParam(required = false) String description,
            @RequestParam(required = false) String shortDescription,
            @RequestParam(required = false) UUID id,
            @RequestParam(required = false) Instant createdAt,
            @RequestParam(required = false) Instant updatedAt,
            @RequestParam(required = false) Instant deletedAt,
            @RequestParam(required = false) String order,
            @RequestParam(required = false) Integer pageIndex,
            @RequestParam(required = false) Integer pageSize) {
        return searchHandler.handle(new SearchCategoriesQuery(name, description, shortDescription, id,
                createdAt, updatedAt, deletedAt, order, pageIndex, pageSize));
    }

    @GetMapping("/gridify")
    public BaseResultList<CategoryViewModel> gridify(
            @RequestParam(required = false) String filter,
            @RequestParam(required = false) String orderBy,
            @RequestParam(required = false) Integer page,
            @RequestParam(required = false) Integer pageSize) {
        return searchHandler.handle(new io.github.mzet97.eestoque.product.application.GridifyCategoriesQuery(
                filter, orderBy, page, pageSize, false));
    }

    @GetMapping("/{id}")
    public BaseResult<CategoryViewModel> getById(@PathVariable UUID id) {
        return getByIdHandler.handle(new GetCategoryByIdQuery(id));
    }

    @PostMapping
    public ResponseEntity<BaseResult<CategoryViewModel>> create(@Valid @RequestBody CreateCategoryCommand command) {
        var id = createHandler.handle(command);
        var result = getByIdHandler.handle(new GetCategoryByIdQuery(id));
        return ResponseEntity.created(URI.create("/api/Categories/" + id)).body(result);
    }

    @PutMapping("/{id}")
    public BaseResult<CategoryViewModel> update(@PathVariable UUID id,
                                                @Valid @RequestBody UpdateCategoryCommand command) {
        var updatedId = updateHandler.handle(new UpdateCategoryCommand(id, command.name(), command.description(),
                command.shortDescription()));
        return getByIdHandler.handle(new GetCategoryByIdQuery(updatedId));
    }

    @DeleteMapping("/{id}")
    public Map<String, Object> delete(@PathVariable UUID id) {
        deleteHandler.handle(new DeleteCategoryCommand(id));
        return Map.of();
    }
}
```
